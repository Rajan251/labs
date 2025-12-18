class PrimaryReplicaRouter:
    def db_for_read(self, model, **hints):
        """
        Reads go to 'replica' database.
        """
        return 'replica'

    def db_for_write(self, model, **hints):
        """
        Writes always go to 'default' (primary).
        """
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if both objects are in the same pool.
        """
        db_set = {'default', 'replica'}
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure migrations only apply to default.
        """
        return db == 'default'
