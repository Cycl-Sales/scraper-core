def migrate(cr, version):
    # Add hi_res_image_link column if it doesn't exist
    cr.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = 'zillow_property' 
                AND column_name = 'hi_res_image_link'
            ) THEN
                ALTER TABLE zillow_property ADD COLUMN hi_res_image_link varchar;
            END IF;
        END $$;
    """)

    # Add hdp_url column if it doesn't exist
    cr.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = 'zillow_property' 
                AND column_name = 'hdp_url'
            ) THEN
                ALTER TABLE zillow_property ADD COLUMN hdp_url varchar;
            END IF;
        END $$;
    """) 