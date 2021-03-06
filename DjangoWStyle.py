import pickle
from vectorformats.Feature import Feature
from vectorformats.Formats.Format import Format

class DjangoWStyle(Format):
    """ This class is designed to decode a Django QuerySet object into
        Feature.Vector objects, with some additonal properties and
        style settings for Leaflet (leaflet.cloudmade.com). 
        
        Simply pass a query_set to the decode method, and it will return
        a list of Features.

        Example Usage:
        
        >>> from vectorformats.Formats import DjangoWStyle, GeoJSON
        >>> qs = Model.objects.filter(city="Cambridge")
        >>> djf = Django.Django(geodjango="geometry", 
                                properties=['city', 'state'],
                                style={'color': '#004070', 'weight': 4})
        >>> geoj = GeoJSON.GeoJSON()
        >>> string = geoj.encode(djf.decode(qs))
        >>> print string 
    """

    geodjango = False 
    """
    If you have GeoDjango geometry columns, set this to the name of the 
    geometry column. 
    """

    pickled_geometry = False
    """If you are not using GeoDjango, but have instead stored your geometry
       as pickled GeoJSON geometries in a column in GeoDjango, set 
       the pickled_geometry=True option in your class constructor. 
    """
    
    pickled_properties = False 
    """A column in the database representing a pickled set of attributes.
    This will be used in addition to any properties in the 'properties' list,
    with the list as a preference.
    """

    properties = []
    """
    List of properties you want copied from the model to the 
    output object.
    """

    style = {}
    """ For use with Leaflet (leaflet.cloudmade.com).
    Leaflet looks for the key 'style' in GeoJSON object and uses those 
    settings to style the GeoJSON layer. For a list of accepted parameters: 
    http://leaflet.cloudmade.com/reference.html#path-options
    To see how to style a GeoJSON layer, see the "Styling Features" section
    here: http://leaflet.cloudmade.com/examples/geojson.html 
    """

    relation_data = {}
    """Used to retrieve values and aggregrate data from related models, 
    which are not direct attributes of res, such as object_set, and 
    object_set.count() The dictionary should be set up as follows:
    { 'method' : ['model']}. The results are added to the properties 
    object as 'model_method' : value.
    
    Currently, the supported keys are 'set_count', 'values_list' and 'display'
    set_count executes object_set.count() on the specified model.
    values_list executes related_model.values_list for the specified model,
    which should be plural.
    display gets the display name from a CHOICES object for the specified
    field (which is specified in place of model)
    """

    def decode(self, query_set, generator = False):
        results = []
        for res in query_set:
            feature = Feature(res.id)
            
            if self.pickled_geometry:
                feature.geometry = pickle.loads(res.geometry)
            
            elif self.geodjango:
                geom = getattr(res, self.geodjango)
                geometry = {}
                geometry['type'] = geom.geom_type
                geometry['coordinates'] = geom.coords
                feature.geometry = geometry

            if self.pickled_properties:
                props = getattr(res, self.pickled_properties) 
                feature.properties = pickle.loads(props.encode("utf-8"))
            
            if self.properties:   
                for p in self.properties:
                    feature.properties[p] = getattr(res, p)

            if self.style:
                feature.properties['style'] = self.style

            if self.relation_data:
                for method,models in self.relation_data.iteritems():
                        if method == 'set_count':
                            for model in models:
                                try:
                                    result = getattr(res,model + '_set')
                                    count = getattr(result,'count')
                                    feature.properties[model + '_' + method] = count()
                                except AttributeError, err:
                                    feature.properties[model + '_' + method] = 'AttributeError'
                        if method == 'values_list':
                            for model in models:
                                try:
                                    result = getattr(res,model)
                                    all_list = list(result.values_list())
                                    feature.properties[model + '_' + method] = all_list
                                except AttributeError, err:
                                    feature.properties[model + '_' + method] = 'AttributeError'
                        if method == 'display' :
                            for model in models:
                                try:
                                    display = 'get_%s_display' % (model)
                                    result = getattr(res,display)
                                    feature.properties[model + '_' + method] = result()
                                except AttributeError, err:
                                    feature.properties[model + '_' + method] = 'AttributeError'
                    
            results.append(feature) 
        return results    
