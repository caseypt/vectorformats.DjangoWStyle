#vectorformats.DjangoWStyle v 0.2.0#

##Overview##

DjangoWStyle is a custom Format for the Python library vectorformats (http://packages.python.org/vectorformats/). DjangoWStyle extends the Django format in two ways:
1. It adds an arbitrary `style` object to the `property` key. This is useful when working with a mapping library that can process GeoJSON layers (like Leaflet: http://leaflet.cloudmade.com).
2. It provides a way to get related attributes of a queryset that are not direct attributes of the queryset being serialized (like foo.bar_set.count(), for instance).

##Functionality##

###Style
Leaflet looks for the key 'style' when parsing a GeoJSON object. It then uses the key/value pairs in the style object to style the GeoJSON features on the map. Here is a basic usage example:

	>>> from vectorformats.Formats import DjangoWStyle, GeoJSON
	>>> qs = Model.objects.filter(city="Cambridge")
	>>> djf = DjangoWStyle.DjangoWStyle(geodjango="geometry", 
							properties=['city', 'state'],
							style={'color': '#004070', 'weight': 4})
	>>> geoj = GeoJSON.GeoJSON()
	>>> geoj.encode(djf.decode(qs))


For a list of the style parameters that Leaflet accepts, visit: http://leaflet.cloudmade.com/reference.html#path-options

For more information on styling GeoJSON layers in Leaflet, see the "Styling Features" section here: http://leaflet.cloudmade.com/examples/geojson.html

###Related Data

DjangoWStyle can retrieve attributes and aggregate information from related models.

DjangoWStyle provides a `relation_data` kwarg that expects a dictionary in the following format: 
	
	{'method_name': ['model_a_name','model_b_name']} 

__At the moment (v. 0.2.0), the supported keys are `'set_count'`, `'values_list'` and `'display'`; which are documented below.__ The value for each method should be a list of models (or field names depending on which method you are using) that you want to preform the method on.

####set_count####
Assume the following Model setup:

	class Street(models.Model)
		name = models.CharField("Name",max_length=100)

		SUFFIX_CHOICES = (
			('ave','Avenue'),
			('st','Street'),
			('rd','Road'))

		suffix=models.CharField("Street Postfix",max_length=10,choices=SUFFIX_CHOICES)
		geometry = models.LineStringField()

  	class City(models.Model):
		name = models.CharField("Name",max_length=50)
		state = models.ForeignKey("State")
		streets = models.ManyToManyField("Street")
		geometry = models.PointField()

	class State(models.Model):
		name = models.CharField("Name",max_length=50)
		geometry = models.PolygonField()

To get the number of cities in Pennsylvania, you would execute:
	
	>>> pa = State.objects.get(name="Pennsylvania")
	>>> pa.city_set.count()

To serialize the aggregate count along with the rest of the State QuerySet data for Pennsylvania:

	>>> from vectorformats.Formats import DjangoWStyle, GeoJSON
	>>> qs = State.objects.filter(name="Pennsylvania")
	>>> djf = DjangoWStyle.DjangoWStyle(geodjango="geometry", 
							properties=['name'],
							style={},
							relation_data = {'set_count': ['city']})
	>>> geoj = GeoJSON.GeoJSON()
	>>> geoj.encode(djf.decode(qs))

The above code will add the following key/value to the GeoJSON `property` object, assuming the count was 200 (as an example):

	'city_set_count' : 200

If any of the queries fail, which is most likely to be caused by there being no relation between the model being serialized and the specified related model, the output will be:
	
	'city_set_count' : 'AttributeError'

If you passed multiple models in the value list, and for example, one of the models is not found, the output will be:
	
	'model_a_set_count' : 5,
	'model_b_set_count' : 'AttributeError',
	'model_c_set_count'	: 6

####values_list####
Specifing 'values_list' as the key in `relation_data` will serialize the fields of a ManyToMany related model. Using the above model setup, here is how to serialize a list of all the associated streets for the city being serialized:

	>>> from vectorformats.Formats import DjangoWStyle, GeoJSON
	>>> qs = City.objects.filter(name="Philadelphia")
	>>> djf = DjangoWStyle.DjangoWStyle(geodjango="geometry", 
							properties=['name'],
							style={},
							relation_data = {'values_list': ['streets']})
	>>> geoj = GeoJSON.GeoJSON()
	>>> geoj.encode(djf.decode(qs))

__Note that the value is `streets` and not `street`.__ Unlike `set_count`, specify the name of the fields (which should be the pluralized name of the related model) that you want the `value_list` for, and not the model name. Assuming that "Broad", "Market", and "Baltimore" are all entries in the Streets model and have a ManyToMany relationship with the City entry "Philadelphia", the above code will add the following to the `property` object of the GeoJSON output for "Philadelphia":
	
	'streets_values_list': [[1,'Broad'],[2,'Market'],[3,'Baltimore']]

Or, more generically:

	'fieldname_values_list': [[pk,field1,field2,...],[pk,field1,field2,...]]

####display####
The `display` method is used to retrieve the display name from a `CHOICES` tuple. Using the model setup noted above, if you wanted to retrieve the display name of the street suffix for the entry "Broad":
	
	>>> from vectorformats.Formats import DjangoWStyle, GeoJSON
	>>> qs = Street.objects.filter(name="Broad")
	>>> djf = DjangoWStyle.DjangoWStyle(geodjango="geometry", 
							properties=['name'],
							style={},
							relation_data = {'display': ['suffix']})
	>>> geoj = GeoJSON.GeoJSON()
	>>> geoj.encode(djf.decode(qs))

Assuming the suffix value for the entry "Broad" was "st", the above code will add the following to the `property` object of the GeoJSON output for "Broad":
	
	'suffix_display': 'Street'