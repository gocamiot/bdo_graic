import os
import json
import numpy as np
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from apps.file_manager.models import File, FileManager, FileChunk, DefaultValues
from apps.tables.models import ActionStatus, DocumentStatus, DocumentType
from apps.common.models import Sidebar
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from pathlib import Path
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import Group
from django.conf import settings
from django.core.files.storage import default_storage
from loader.models import is_pgvector_enabled
from apps.common.signals import to_sql_vector
from apps.graic.utils import extract_keywords

# Create your views here.

@login_required
def file_manager(request):
    file_managers = FileManager.objects.filter(parent=None, action_status=ActionStatus.IS_ACTIVE).order_by('-created_at')

    context = {
        'file_managers': file_managers,
        'document_status': DocumentStatus,
        'document_type': DocumentType
    }
    return render(request, 'file_manager/index.html', context)

@login_required
def sub_folders(request, slug):
    search = request.GET.get('search')
    default_value = DefaultValues.objects.first()
    parent_folder = get_object_or_404(FileManager, slug=slug)
    root_folder = parent_folder
    while root_folder.parent is not None:
        root_folder = root_folder.parent

    file_managers = FileManager.objects.filter(
        parent=parent_folder, action_status=ActionStatus.IS_ACTIVE
    ).order_by('-created_at')

    files = list(File.objects.filter(
        file_manager=parent_folder, action_status=ActionStatus.IS_ACTIVE
    ).order_by('-uploaded_at'))

    if search and is_pgvector_enabled():
        # if default_value and default_value.extract_keywords:
        #     keywords = extract_keywords(search)
        # else:
        #     keywords = search

        keywords = search
        print(keywords, "====keywords====")

        search_vector = to_sql_vector(keywords)

        all_chunk_similarities = []

        file_chunks_map = {}
        for file in files:
            chunks = FileChunk.objects.filter(file=file).exclude(vector=None)
            if not chunks.exists():
                continue

            chunk_similarities = []
            for chunk in chunks:
                similarity = np.dot(np.array(chunk.vector), np.array(search_vector)) / (
                    np.linalg.norm(chunk.vector) * np.linalg.norm(search_vector)
                )
                similarity = round(float(similarity), 3)
                chunk_similarities.append((similarity, chunk))

            file_chunks_map[file] = chunk_similarities
            all_chunk_similarities.extend(chunk_similarities)

        if default_value and default_value.dynamic_similarity and default_value.dynamic_rows:
            sorted_all_chunks = sorted(all_chunk_similarities, key=lambda x: x[0], reverse=True)
            if len(sorted_all_chunks) >= int(default_value.dynamic_rows):
                nth_index = int(default_value.dynamic_rows) - 1
                nth_similarity = sorted_all_chunks[nth_index][0]
            else:
                nth_similarity = sorted_all_chunks[0][0]
        else:
            nth_similarity = None

        for file, chunk_similarities in file_chunks_map.items():
            matched_locations = []
            max_similarity = 0

            for sim, chunk in chunk_similarities:
                if default_value and default_value.dynamic_similarity and nth_similarity is not None:
                    if sim >= nth_similarity:
                        matched_locations.append({
                            "page": chunk.page_number,
                            "position": chunk.position,
                            "similarity": sim
                        })
                else:
                    similarity_threshold = (
                        int(default_value.similarity_threshold) / 100
                        if default_value and default_value.similarity_threshold
                        else 0.3
                    )
                    if sim >= similarity_threshold:
                        matched_locations.append({
                            "page": chunk.page_number,
                            "position": chunk.position,
                            "similarity": sim
                        })

                if matched_locations:
                    max_similarity = max([loc["similarity"] for loc in matched_locations])

            if matched_locations:
                file.similarity = max_similarity
                file.matched_locations = matched_locations

        files = sorted(
            [f for f in files if hasattr(f, "matched_locations")],
            key=lambda f: f.similarity,
            reverse=True
        )

    context = {
        'file_managers': file_managers,
        'parent_folder': parent_folder,
        'files': files,
        'document_status': DocumentStatus,
        'document_type': DocumentType,
        'segment': root_folder.name,
        'parent': root_folder.sidebar.segment if root_folder.sidebar else "",
        'default_value': default_value
    }
    return render(request, 'file_manager/sub_folders.html', context)


@login_required
def create_folder(request, slug=None):
    parent_folder = None
    if slug:
        parent_folder = get_object_or_404(FileManager, slug=slug)

    if request.method == 'POST':
        name = request.POST.get('name')
        file_manager = FileManager.objects.create(
            name=name,
            created_by=request.user,
            updated_by=request.user,
            parent=parent_folder
        )

        group_name = request.POST.get('group_name')
        if sidebar_id := request.POST.get('sidebar'):
            sidebar = get_object_or_404(Sidebar, pk=sidebar_id)
            file_manager.sidebar = sidebar
            file_manager.save()

            group = get_object_or_404(Group, name=group_name)
            dynamic_url = reverse('sub_folders', kwargs={'slug': file_manager.slug})

            Sidebar.objects.create(
                group=group,
                name=name,
                dynamic_url=dynamic_url,
                segment=name,
                parent=sidebar
            )

        return redirect(request.META.get('HTTP_REFERER'))

    return redirect(request.META.get('HTTP_REFERER'))

@login_required
def upload_file_to_folder(request):
    if request.method == 'POST' and request.FILES.getlist('files'):
        folder_id = request.POST.get('folder_id')
        base_folder = get_object_or_404(FileManager, id=folder_id)

        files = request.FILES.getlist('files')
        paths = request.POST.getlist('paths[]')

        folder_hierarchy = set()
        for relative_path in paths:
            path_obj = Path(relative_path)
            *parts, _ = path_obj.parts
            for i in range(1, len(parts)+1):
                folder_hierarchy.add('/'.join(parts[:i]))

        created_folders = {} 
        for folder_path in sorted(folder_hierarchy):
            parts = folder_path.split('/')
            parent = base_folder
            current_path = ''
            
            for part in parts:
                current_path = f"{current_path}/{part}" if current_path else part
                
                if current_path in created_folders:
                    parent = created_folders[current_path]
                    continue
                
                new_name = part
                counter = 1
                while FileManager.objects.filter(name=new_name, parent=parent, action_status=ActionStatus.IS_ACTIVE).exists():
                    new_name = f"{part}_copy" if counter == 1 else f"{part}_copy{counter}"
                    counter += 1
                
                folder, created = FileManager.objects.get_or_create(
                    name=new_name,
                    parent=parent,
                    action_status=ActionStatus.IS_ACTIVE,
                    defaults={
                        'created_by': request.user,
                        'updated_by': request.user
                    }
                )
                created_folders[current_path] = folder
                parent = folder

        for uploaded_file, relative_path in zip(files, paths):
            path_obj = Path(relative_path)
            *parts, filename = path_obj.parts
            folder_path = '/'.join(parts)
            
            target_folder = created_folders.get(folder_path, base_folder)
            
            File.objects.create(
                file_manager=target_folder,
                file=uploaded_file,
                uploaded_by=request.user,
                updated_by=request.user
            )

        return JsonResponse({'message': f'{len(files)} file(s) uploaded successfully'})

    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def edit_folder(request, pk):
    folder = get_object_or_404(FileManager, pk=pk)
    if request.method == 'POST':
        for attribute, value in request.POST.items():
            if attribute == 'csrfmiddlewaretoken':
                continue

            setattr(folder, attribute, value)
            folder.save()

        return redirect(request.META.get('HTTP_REFERER'))

    return redirect(request.META.get('HTTP_REFERER'))

@login_required
def delete_folder(request, pk):
    folder = get_object_or_404(FileManager, pk=pk)

    parts = []
    file_manager = folder
    while file_manager:
        parts.insert(0, file_manager.name)
        file_manager = file_manager.parent

    old_path = os.path.join(settings.MEDIA_ROOT, *parts)

    if os.path.exists(old_path) and os.path.isdir(old_path):
        parent_dir = os.path.dirname(old_path)
        new_folder_name = f"del_{folder.name}"
        new_path = os.path.join(parent_dir, new_folder_name)

        try:
            os.rename(old_path, new_path)
            folder.name = new_folder_name
        except Exception as e:
            print(f"Error renaming folder: {e}")

    folder.delete()

    return redirect(request.META.get('HTTP_REFERER'))


@login_required
def edit_file(request, pk):
    file = get_object_or_404(File, pk=pk)

    if request.method == 'POST':
        new_name = request.POST.get('name', '').strip()
        old_name = os.path.basename(file.file.name)

        if new_name and new_name != old_name:
            old_path = file.file.path
            dir_path = os.path.dirname(old_path)
            new_path = os.path.join(dir_path, new_name)

            if not default_storage.exists(new_path):
                with default_storage.open(old_path, 'rb') as f:
                    default_storage.save(new_path, f)
                default_storage.delete(old_path)

                relative_path = os.path.relpath(new_path, settings.MEDIA_ROOT)
                file.file.name = relative_path

        for attribute, value in request.POST.items():
            if attribute in ['csrfmiddlewaretoken', 'name']:
                continue
            setattr(file, attribute, value)

        file.updated_by = request.user
        file.save()

        return redirect(request.META.get('HTTP_REFERER'))

    return redirect(request.META.get('HTTP_REFERER'))


@login_required
def delete_file(request, pk):
    file_obj = get_object_or_404(File, pk=pk)

    if not file_obj.file:
        file_obj.delete()
        return redirect(request.META.get('HTTP_REFERER'))

    try:
        try:
            old_path = file_obj.file.path
        except Exception:
            old_path = os.path.join(settings.MEDIA_ROOT, file_obj.file.name)

        if os.path.exists(old_path):
            dir_name, file_name = os.path.split(old_path)
            new_file_name = f"del_{file_name}"
            new_path = os.path.join(dir_name, new_file_name)
            os.rename(old_path, new_path)

            file_obj.file.name = os.path.relpath(new_path, settings.MEDIA_ROOT)
        else:
            storage = getattr(file_obj.file, 'storage', None)
            if storage:
                try:
                    storage.delete(file_obj.file.name)
                except Exception:
                    pass

        file_obj.delete()
    except Exception as e:
        print("Error deleting file:", e)

    return redirect(request.META.get('HTTP_REFERER'))


@login_required
@csrf_exempt
def delete_selected_items(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            items = data.get('items', [])

            for item in items:
                # Delete FILE
                if item.startswith('file-'):
                    pk = item.replace('file-', '')
                    file = File.objects.filter(pk=pk).first()
                    if file and file.file:
                        old_path = file.file.path
                        dir_name, file_name = os.path.split(old_path)
                        new_file_name = f"del_{file_name}"
                        new_path = os.path.join(dir_name, new_file_name)

                        if os.path.exists(old_path):
                            os.rename(old_path, new_path)
                            relative_path = os.path.relpath(new_path, settings.MEDIA_ROOT)
                            file.file.name = relative_path

                        file.delete()

                # Delete FOLDER
                elif item.startswith('folder-'):
                    pk = item.replace('folder-', '')
                    folder = FileManager.objects.filter(pk=pk).first()
                    if folder:
                        parts = []
                        file_manager = folder
                        while file_manager:
                            parts.insert(0, file_manager.name)
                            file_manager = file_manager.parent

                        old_path = os.path.join(settings.MEDIA_ROOT, *parts)

                        if os.path.exists(old_path) and os.path.isdir(old_path):
                            parent_dir = os.path.dirname(old_path)
                            new_folder_name = f"del_{folder.name}"
                            new_path = os.path.join(parent_dir, new_folder_name)

                            try:
                                os.rename(old_path, new_path)
                                folder.name = new_folder_name
                            except Exception as e:
                                print(f"Error renaming folder: {e}")

                        folder.delete()

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


def set_default_value(request):
    if request.method == 'POST':
        similarity_threshold = request.POST.get('similarity_threshold')
        dynamic_rows = request.POST.get('dynamic_rows')
        filter_method = request.POST.get('filter_method')
        dynamic_similarity = request.POST.get('dynamic_similarity') == 'on'
        extract_keywords = request.POST.get('extract_keywords') == 'on'

        DefaultValues.objects.all().delete()
        if similarity_threshold:
            DefaultValues.objects.create(
                similarity_threshold=similarity_threshold if similarity_threshold else None,
                extract_keywords=extract_keywords,
                filter_method=filter_method,
                dynamic_similarity=False,
                dynamic_rows=None
            )
        elif dynamic_similarity and dynamic_rows: 
            DefaultValues.objects.create(
                similarity_threshold=None,
                extract_keywords=extract_keywords,
                filter_method=filter_method,
                dynamic_similarity=dynamic_similarity,
                dynamic_rows=dynamic_rows if dynamic_rows else None
            )
        else:
            DefaultValues.objects.create(
                extract_keywords=extract_keywords,
                filter_method=filter_method
            )

        return redirect(request.META.get('HTTP_REFERER'))
    
    return redirect(request.META.get('HTTP_REFERER'))


def clear_default(request):
    DefaultValues.objects.all().delete()
    return redirect(request.META.get('HTTP_REFERER'))