def init_controllers(app):
    import application.controller.user_api 
    import application.controller.helper_common_api
    import application.controller.upload
    import application.controller.diagnosis

    #controller la noi viet API (function thuc hien 1 chuc nang: upload, log in ,...)