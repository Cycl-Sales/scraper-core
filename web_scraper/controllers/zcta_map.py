from odoo import http
from odoo.http import request, Response
import geopandas as gpd
import os

class ZctaMapController(http.Controller):
    @http.route('/zcta/map', type='http', auth='none')
    def zcta_map(self, **kw):
        return request.render('web_scraper.zcta_map_template', {})

    @http.route('/zcta/geojson', type='http', auth='none')
    def zcta_geojson(self, **kw):
        base = request.env['ir.config_parameter'].sudo().get_param('web_scraper.data_dir') or '/Users/rscs/odoo/odoo18/custom/web_scraper/common/tl_2020_us_zcta520'
        shp_path = os.path.join(base, 'tl_2020_us_zcta520.shp')
        gdf = gpd.read_file(shp_path)
        # For demo, simplify geometry to reduce size
        gdf = gdf.to_crs(epsg=4326)
        geojson = gdf.simplify(0.01).to_json()
        return Response(geojson, content_type='application/json')