#chua cac def su dung nhieu lan
import random
import datetime
import inspect
import uuid #kieu du lieu sinh random string -> tao identify luu vao database

from cryptography.fernet import Fernet  #ma hoa password
from application import app
import string
from sqlalchemy import Date
from sqlalchemy import DateTime
from sqlalchemy import Interval
from sqlalchemy.exc import NoInspectionAvailable
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.associationproxy import AssociationProxy
from sqlalchemy.ext import hybrid
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import ColumnProperty
from sqlalchemy.orm import RelationshipProperty as RelProperty
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm.attributes import QueryableAttribute
from sqlalchemy.orm.query import Query
from sqlalchemy.sql import func
from sqlalchemy.sql.expression import ColumnElement
from sqlalchemy.inspection import inspect as sqlalchemy_inspect


#: Names of attributes which should definitely not be considered relations when
#: dynamically computing a list of relations of a SQLAlchemy model.
RELATION_BLACKLIST = ('query', 'query_class', '_sa_class_manager',
                      '_decl_class_registry')


#: Names of columns which should definitely not be considered user columns to
#: be included in a dictionary representation of a model.
COLUMN_BLACKLIST = ('_sa_polymorphic_on', )

#: Types which should be considered columns of a model when iterating over all
#: attributes of a model class.
COLUMN_TYPES = (InstrumentedAttribute, hybrid_property)

#: Strings which, when received by the server as the value of a date or time
#: field, indicate that the server should use the current time when setting the
#: value of the field.
CURRENT_TIME_MARKERS = ('CURRENT_TIMESTAMP', 'CURRENT_DATE', 'LOCALTIMESTAMP')


def current_uid(request):
    user_token = request.headers.get("X-USER-TOKEN", None)
    if user_token is None:
        return None
    uid = redisdb.get("sessions:" + user_token)
    if uid is not None:
        p = redisdb.pipeline()
        p.set("sessions:" + user_token, uid)
        p.expire("sessions:" + user_token, app.config.get('SESSION_EXPIRED', 86400))
        p.execute()
        return uid.decode('utf8')
    
    return None


def generator_salt():
    """
    Generates a key and save it into a file
    """
    salt = Fernet.generate_key()
    return salt.decode('utf-8')


''' Xử lý auth password '''
def encrypt_password(password, key = None):
    """
    Encrypts a password
    """
    if key is None:
        key = app.config.get("SECRET_KEY", "toiyeuvietnam")
    encoded_password = password.encode()
    f = Fernet(key)
    encrypted_password = f.encrypt(encoded_password)

    return encrypted_password.decode('utf-8')


def decrypt_password(encrypted_password, key = None):
    """
    Decrypts an encrypted password
    """
    if key is  None:
        key = app.config.get("SECRET_KEY", "toiyeuvietnam")
    f = Fernet(key)
    encrypted_password = str.encode(encrypted_password)
    decrypted_password = f.decrypt(encrypted_password)


    return decrypted_password.decode('utf-8')


def response_current_user(user):
    response = {}
    # token = generate_user_token(user.id)
    response["id"] = user.id
    response["hoten"] = user.hoten
    response["dienthoai"] = user.dienthoai
    response["email"] = user.email
    response["active"] = user.active
    response["taikhoan"] = user.taikhoan

    roles = []
    if user.vaitro is not None:
        for role in user.vaitro:
            roles.append(role.vaitro)
    response["vaitro"] = roles
    return response


def to_dict(instance, deep=None, exclude=None, include=None,
            exclude_relations=None, include_relations=None,
            include_methods=None):
    """Returns a dictionary representing the fields of the specified `instance`
    of a SQLAlchemy model.

    The returned dictionary is suitable as an argument to
    :func:`flask.jsonify`; :class:`datetime.date` and :class:`uuid.UUID`
    objects are converted to string representations, so no special JSON encoder
    behavior is required.

    `deep` is a dictionary containing a mapping from a relation name (for a
    relation of `instance`) to either a list or a dictionary. This is a
    recursive structure which represents the `deep` argument when calling
    :func:`!_to_dict` on related instances. When an empty list is encountered,
    :func:`!_to_dict` returns a list of the string representations of the
    related instances.

    If either `include` or `exclude` is not ``None``, exactly one of them must
    be specified. If both are not ``None``, then this function will raise a
    :exc:`ValueError`. `exclude` must be a list of strings specifying the
    columns which will *not* be present in the returned dictionary
    representation of the object (in other words, it is a
    blacklist). Similarly, `include` specifies the only columns which will be
    present in the returned dictionary (in other words, it is a whitelist).

    .. note::

       If `include` is an iterable of length zero (like the empty tuple or the
       empty list), then the returned dictionary will be empty. If `include` is
       ``None``, then the returned dictionary will include all columns not
       excluded by `exclude`.

    `include_relations` is a dictionary mapping strings representing relation
    fields on the specified `instance` to a list of strings representing the
    names of fields on the related model which should be included in the
    returned dictionary; `exclude_relations` is similar.

    `include_methods` is a list mapping strings to method names which will
    be called and their return values added to the returned dictionary.

    """
    if (exclude is not None or exclude_relations is not None) and \
            (include is not None or include_relations is not None):
        raise ValueError('Cannot specify both include and exclude.')
    # create a list of names of columns, including hybrid properties
    instance_type = type(instance)
    columns = []
    try:
        inspected_instance = sqlalchemy_inspect(instance_type)
        column_attrs = inspected_instance.column_attrs.keys()
        descriptors = inspected_instance.all_orm_descriptors.items()
        hybrid_columns = [k for k, d in descriptors
                          if d.extension_type == hybrid.HYBRID_PROPERTY
                          and not (deep and k in deep)]
        columns = column_attrs + hybrid_columns
    except NoInspectionAvailable:
        return instance
    # filter the columns based on exclude and include values
    if exclude is not None:
        columns = (c for c in columns if c not in exclude)
    elif include is not None:
        columns = (c for c in columns if c in include)
    # create a dictionary mapping column name to value
    result = dict((col, getattr(instance, col)) for col in columns
                  if not (col.startswith('__') or col in COLUMN_BLACKLIST))
    # add any included methods
    if include_methods is not None:
        for method in include_methods:
            if '.' not in method:
                value = getattr(instance, method)
                # Allow properties and static attributes in include_methods
                if callable(value):
                    value = value()
                result[method] = value
    # Check for objects in the dictionary that may not be serializable by
    # default. Convert datetime objects to ISO 8601 format, convert UUID
    # objects to hexadecimal strings, etc.
    for key, value in result.items():
        if isinstance(value, (datetime.date, datetime.time)):
            result[key] = value.isoformat()
        elif isinstance(value, uuid.UUID):
            result[key] = str(value)
        elif key not in column_attrs and is_mapped_class(type(value)):
            result[key] = to_dict(value)
    # recursively call _to_dict on each of the `deep` relations
    deep = deep or {}
    for relation, rdeep in deep.items():
        # Get the related value so we can see if it is None, a list, a query
        # (as specified by a dynamic relationship loader), or an actual
        # instance of a model.
        relatedvalue = getattr(instance, relation)
        if relatedvalue is None:
            result[relation] = None
            continue
        # Determine the included and excluded fields for the related model.
        newexclude = None
        newinclude = None
        if exclude_relations is not None and relation in exclude_relations:
            newexclude = exclude_relations[relation]
        elif (include_relations is not None and
              relation in include_relations):
            newinclude = include_relations[relation]
        # Determine the included methods for the related model.
        newmethods = None
        if include_methods is not None:
            newmethods = [method.split('.', 1)[1] for method in include_methods
                          if method.split('.', 1)[0] == relation]
        if is_like_list(instance, relation):
            result[relation] = [to_dict(inst, rdeep, exclude=newexclude,
                                        include=newinclude,
                                        include_methods=newmethods)
                                for inst in relatedvalue]
            continue
        # If the related value is dynamically loaded, resolve the query to get
        # the single instance.
        if isinstance(relatedvalue, Query):
            relatedvalue = relatedvalue.one()
        result[relation] = to_dict(relatedvalue, rdeep, exclude=newexclude,
                                   include=newinclude,
                                   include_methods=newmethods)
    return result


def convert_text_khongdau(text):
    if text is None:
        return None
    kituA=["á","à","ạ","ã","ả","â","ấ","ầ","ậ","ẫ","ẩ","ă","ặ","ằ","ắ","ẳ","ẵ"]
    kituE=["é","è","ẹ","ẻ","ẽ","ê","ế","ề","ệ","ễ","ể"]
    kituI=["í","ì","ị","ỉ","ĩ"]
    kituO=["ò","ó","ọ","ỏ","õ","ô","ồ","ố","ộ","ổ","ỗ","ơ","ờ","ớ","ợ","ở","ỡ"]
    kituU=["ù","ú","ụ","ủ","ũ","ư","ừ","ứ","ự","ử","ữ"]
    kituY=["ỳ","ý","ỵ","ỷ","ỹ"]

    ten = text.lower()
    for i in ten:
        if i in kituA:
            ten = ten.replace(i,"a")
        elif i in kituE:
            ten = ten.replace(i,"e")
        elif i in kituI:
            ten = ten.replace(i,"i")
        elif i in kituO:
            ten = ten.replace(i,"o")
        elif i in kituU:
            ten = ten.replace(i,"u")
        elif i in kituY:
            ten = ten.replace(i,"y")
        elif i=="đ":
            ten = ten.replace(i,"d")
    return ten

def default_uuid():
    return str(uuid.uuid4())