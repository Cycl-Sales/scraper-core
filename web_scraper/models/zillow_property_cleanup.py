from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class ZillowPropertyCleanup(models.Model):
    _name = 'zillow.property.cleanup'
    _description = 'Zillow Property Cleanup'

    def cleanup_properties_without_details(self):
        """
        Cron job to clean up zillow.property records that don't have associated zillow.property.detail records.
        This job runs every 24 hours.
        """
        try:
            # Find all zillow.property records
            properties = self.env['zillow.property'].search([])
            properties_to_delete = []

            for property in properties:
                # Check if there's no associated detail record
                detail = self.env['zillow.property.detail'].search([
                    ('property_id', '=', property.id)
                ], limit=1)
                
                if not detail:
                    properties_to_delete.append(property.id)
                    _logger.info(f"Property {property.id} ({property.street_address}) will be deleted - no detail record found")

            # Delete the properties in batches to avoid memory issues
            if properties_to_delete:
                self.env['zillow.property'].browse(properties_to_delete).unlink()
                _logger.info(f"Successfully deleted {len(properties_to_delete)} properties without detail records")
            else:
                _logger.info("No properties found without detail records")

        except Exception as e:
            _logger.error(f"Error in cleanup_properties_without_details: {str(e)}")
            raise 