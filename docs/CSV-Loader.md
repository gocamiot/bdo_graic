## CSV Loader

Date conversion 

```python
time.mktime(datetime.datetime.strptime('Nov 30 2011 22:00PM', "%b %d %Y %H:%M%p").timetuple()) 
1322683200.0
```

```python
datetime.datetime.utcfromtimestamp( 1322690400 ).strftime('%b %d %Y %H:%M%p') 
'Nov 30 2011 22:00PM'
```
