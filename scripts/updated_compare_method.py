    def compare_vin_lists(self, dealership_name: str, current_vins: List[str]) -> Tuple[List[str], List[str]]:
        """Compare current VINs with dealership-specific VIN log to find new vehicles"""
        try:
            # Convert dealership name to table name format
            # Example: "Porsche St. Louis" -> "porsche_st_louis_vin_log"
            table_name = dealership_name.lower().replace(' ', '_').replace('.', '').replace("'", '') + '_vin_log'
            
            # Check if dealership-specific table exists
            table_check = db_manager.execute_query("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            """, (table_name,))
            
            if not table_check:
                logger.warning(f"VIN log table {table_name} does not exist. Creating it...")
                # Create the table if it doesn't exist
                create_sql = f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    vin VARCHAR(17) PRIMARY KEY,
                    processed_date DATE NOT NULL DEFAULT CURRENT_DATE,
                    order_type VARCHAR(20),
                    template_type VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
                db_manager.execute_query(create_sql)
                logger.info(f"Created VIN log table: {table_name}")
            
            # Get previous VINs from dealership-specific table
            query = f"""
                SELECT vin FROM {table_name}
            """
            previous_vins = db_manager.execute_query(query)
            
            previous_vin_set = {row['vin'] for row in previous_vins}
            current_vin_set = set(current_vins)
            
            # Find new VINs (in current but not in previous)
            new_vins = list(current_vin_set - previous_vin_set)
            
            # Find removed VINs (in previous but not in current)
            removed_vins = list(previous_vin_set - current_vin_set)
            
            logger.info(f"[VIN COMPARE] {dealership_name}: {len(new_vins)} new, {len(removed_vins)} removed")
            logger.info(f"[VIN COMPARE] Using table: {table_name}")
            logger.info(f"[VIN COMPARE] Previous VINs in log: {len(previous_vin_set)}, Current inventory: {len(current_vin_set)}")
            
            # Update dealership-specific VIN history
            self._update_dealership_vin_history(dealership_name, table_name, new_vins)
            
            return new_vins, removed_vins
            
        except Exception as e:
            logger.error(f"Error comparing VINs for {dealership_name}: {e}")
            return current_vins, []  # Treat all as new if comparison fails
    
    def _update_dealership_vin_history(self, dealership_name: str, table_name: str, new_vins: List[str]):
        """Update dealership-specific VIN history for tracking"""
        try:
            if not new_vins:
                logger.info(f"No new VINs to add to {table_name}")
                return
                
            # Insert new VINs into dealership-specific table
            for vin in new_vins:
                insert_sql = f"""
                    INSERT INTO {table_name} (vin, processed_date, order_type)
                    VALUES (%s, CURRENT_DATE, 'CAO')
                    ON CONFLICT (vin) DO NOTHING
                """
                db_manager.execute_query(insert_sql, (vin,))
            
            logger.info(f"[VIN HISTORY] Added {len(new_vins)} new VINs to {table_name}")
                
        except Exception as e:
            logger.error(f"Error updating dealership VIN history: {e}")