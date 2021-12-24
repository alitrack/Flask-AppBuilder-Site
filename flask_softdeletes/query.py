from flask_sqlalchemy import BaseQuery as _BaseQuery
from sqlalchemy import event

class SoftDeletedQuery(_BaseQuery):
    def __init__(self, entities, session=None):
        super().__init__(entities, session=session)
    _with_deleted = False

@event.listens_for(SoftDeletedQuery, 'before_compile', retval=True, bake_ok=True)
def _before_compile(query):
    for desc in query.column_descriptions:
        _model = desc['entity']
        if _model is None:
            continue
        if hasattr(_model, 'deleted_time'):
            if not query._with_deleted:
                query = query.enable_assertions(False).filter(_model.deleted_time == 0)
    return query