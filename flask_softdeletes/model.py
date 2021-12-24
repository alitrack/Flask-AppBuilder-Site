import time
from .query import SoftDeletedQuery
from sqlalchemy import Column, Integer


class SoftDeletedMixin:
    query_class = SoftDeletedQuery

    deleted_time = Column(Integer, index=True, nullable=False, default=0, comment='软删除标记时间')

    @property
    def deleted_datetime(self):
        if self.deleted_time:
            return time.strftime('%Y-%m-%d %H:%M', time.localtime(self.deleted_time))
        return ''
    
    def delete(self):
        self.deleted_time = time.time()
        self.__class__.query.session.commit()
        return True
        
    def restore(self):
        self.deleted_time = 0
        self.__class__.query.session.commit()