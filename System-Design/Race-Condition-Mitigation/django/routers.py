class PrimaryReplicaRouter:
    def db_for_read(self, model, **hints):
        """
        Reads go to a random replica (if configured), otherwise default.
        """
        return 'default'

    def db_for_write(self, model, **hints):
        """
        Writes always go to primary.
        """
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return True
