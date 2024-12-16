from framework.services.service_factory import BaseServiceFactory
#import app.resources.course_resource as course_resource
from framework.services.data_access.MySQLRDBDataService import MySQLRDBDataService


# TODO -- Implement this class
class ServiceFactory(BaseServiceFactory):

    def __init__(self):
        super().__init__()

    @classmethod
    def get_service(cls, service_name):
        #
        # TODO -- The terrible, hardcoding and hacking continues.
        #
        if service_name == 'CourseResource':
            result = course_resource.CourseResource(config=None)
        elif service_name == 'CourseResourceDataService':
            context = dict(user="jigglypuff7", password="Jigglypuff7!",
                           host="jigglypuff7.c7s86kaawl6v.us-east-2.rds.amazonaws.com", port=3306)
            data_service = MySQLRDBDataService(context=context)
            result = data_service
        else:
            result = None

        return result




