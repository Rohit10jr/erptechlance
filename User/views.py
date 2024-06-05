from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import User, user_group, user_right, transaction_right
import jwt, datetime
from django.http import JsonResponse
from .serializers import UserGroupSerializer, UserSerializer, UserRightSerializer, TransactionRightSerializer, GetUserRightSerializer
from django.db.models import ProtectedError



# Create your views here.
def verify_token(request):

    try:
        if not (request.headers['Authorization'] == "null"):
            token = request.headers['Authorization']
    except:
        if not (request.COOKIES.get('token') == "null"):
            token = request.COOKIES.get('token')
    else:
        context = {
            "success":False,
            "message":"INVALID_TOKEN",
            }
        payload = JsonResponse(context)
        
    if not token:
        context = {
                "success":False,
                "message":"INVALID_TOKEN",
            }
        payload =  JsonResponse(context)

    try:
        payload = jwt.decode(token, 'secret', algorithm=['HS256'])

    except :
        context = {
                "success":False,
                "message":"INVALID_TOKEN",
            }
        payload =  JsonResponse(context)
    return payload


def get_error(serializerErr):
    err = ''
    for i in serializerErr:
        err = serializerErr[i][0]
        break
    return err


class VerifyUser(APIView):
    def get(self, request):
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        return Response({
                        "success":True,
                        "message":"User logged in successfully",
                        "data":
                            {
                            "user":{
                                "id":user.id,
                                "email":user.email,
                                "is_superuser":user.is_superuser
                                }
                            
                            }
                        })


class LoginView(APIView):
    def post(self, request):
        email = request.data['emial']
        password = request.data['password']
        user = User.objects.filter(email=email).first()

        if user is None:
            
            context = {
                "success":False,
                "message":"User not found",
                "data":
                {
                    "email":email,
                }
            }

            return JsonResponse(context)
        
        if not user.check_password(password):
            context = {
                "success":False,
                "message":"In-correct password",
                "data":
                {
                    "email":email,
                }
            }

            return JsonResponse(context)

        payload = {
                    'id': user.id,
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=500),
                    'iat': datetime.datetime.utcnow()
                    }
        token = jwt.encode(payload, 'secret', algorithm='HS256').decode('utf-8') 
        response = Response()
        response.set_cookie(key='token', value=token, httponly=True)

        response.data = {
                        "success":True,
                        "message":"User logged in successfully",
                        "data":
                            {
                            "accessToken":token,
                            "user":{
                                "id":user.id,
                                "email":user.email,
                                "is_superuser":user.is_superuser,
                                }
                            }
                        }
        
        return response
    
        



class AddUserView(APIView):

    def post(self, request):

        payload = verify_token(request)

        try:
            user= User.objects.filter(id=payload['id']).first()

        except:
            return payload
        
        if user.is_superuser:
            temp = request.data
            context = temp.dict()
            context['altered_by'] = user.email
            serializer = UserSerializer(data=context)

            if not serializer.is_valid():
                return Response({
                "success":False,
                "message":get_error(serializer.errors),
                "data": user.email
                })
            
            serializer.save()
        
            return Response({
                "success":True,
                "message":"User added successfully",
                "data":serializer.data
                })
        else:
            return Response({
                "success":False,
                "message":"Not authorized to create user",
                "data":{
                    "email":user.email
                }
            })



class EditUserView(APIView):

    def put(self, request, id):
        payload = verify_token(request)

        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload

        if user.is_superuser:

            selected_user = User.objects.get(id=id) 
            temp = request.data
            context = temp.dict()
            context['altered_by'] = user.email
            serializer = UserSerializer(selected_user, data=context)

            if not serializer.is_valid():
                return Response({
                    'success':False,
                    'message':get_error(serializer.errors),
                })
            serializer.save()
            return Response({
                'success':True,
                'message':'User edited successfully'
            })
        
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to edit User',
                })


class DeleteUserView(APIView):

    def delete(Self, request, id):
        payload = verify_token(request)

        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        

        if user.is_superuser:
            selected_user = User.objects.get(id=id)
            selected_user.altered_by = user.email

            selected_user.delete() 

            return Response({
                'success':True, 
                'message':'User deelted successfully',
                })
        
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to Delete User Company',
                })



class GetUserView(APIView):
    def get(self, request):
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        if user.is_superuser:
            users = User.objects.all()
            serializer = UserSerializer(users, many=True)

            return Response({
                'success':True,
                'message':'',
                'data':serializer.data
            })
        
        else:
            return Response({
                'success':False,
                'messge': 'you are not allowed to view user details',
                'data':[]
            })




# API for retrieving particular user
# Request : GET    
# Endpoint : get-users/<int:id>
class DetailUserView(APIView):
    def get(self, request, id):
        payload = verify_token(request)

        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        if user.is_superuser:
            user_details = User.objects.get(id=id)
            serializer = UserSerializer(user_details)

            return Response({
                'success':True,
                'messgae':'',
                'data':serializer.data
            })
        
        else:
            return Response({
                'success':False,
                'message':'you are not allowed to view user details',
                'data':[]
            })



# API For creating a user group
# request : POST  
# Endpoint : add-user-group
class AddUserGroup(APIView):

    def post(Self, request):
        payload = verify_token(request)

        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        if user.is_superuser:
            temp = request.data
            context = temp.dict()
            context['altered_by'] = user.email

            serializer = UserGroupSerializer(data=context)

            if not serializer.is_valid():
                return Response({
                    "success":False,
                    "message":get_error(serializer.data),
                    "data":{
                        "email":user.email
                    }
                }) 

            serializer.save()

            user_group_instance = user_group.objects.latest('id')
            all_transactions = transaction_right.objects.all()
            for instance in all_transactions:
                user_right_instance = user_right(user_group_id=user_group_instance, transaction_id=instance,created_by=user.email)
                user_right_instance.save() 

            return Response({
                "success":True,
                "message":"User Groups added successfully",
                "data":serializer.data
                })

        else:
            return Response({
                "success":False,
                "message":"Not authorized to create User Groups",
                "data":{
                    "email":user.email
                }
            })




# API For updating a user group
# Request : PUT
# Endpoint : edit-user-group/<int:id>
class EditUserGroup(APIView):

    def put(self, request, id):
        payload = verify_token(request)

        try:
            user = User.objects.filter(Id=payload['id']).first()
        except:
            return payload

        if user.is_superuser:
            selected_group = user_group.objects.et(id=id)
            temp = request.data
            context = temp.dict()
            context['altered_by'] = user.email
            serializer = UserGroupSerializer(selected_group, data=context)

            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'message': get_error(serializer.errors),
                    })
            
            serializer.save()
    
            return Response({
                'success': True,
                'message': 'User Group Edited successfully'})


        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to edit User Group',
                })


# API For deleting a user group
# Request : DELETE
# Endpoint : delete-user-group/<int:id>
class DeleteUserGroup(APIView):
    def delete(self, request, id):
        payload = verify_token(request)

        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        if user.is_superuser:
            selected_group = user_group.objects.get(id=id)
            selected_group.altered_by = user.email
            try:
                selected_group.delete()
                return Response({
                    'success':True,
                    'message':'User Group deleted Successfully',
                })
            except ProtectedError as e:
                return Response({
                    'success': True,
                    'message': 'Please delete all related rights of '+str(selected_group.user_group_name)+' from user rights first',
                    
                    })
            
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to Delete User Group',
                })



# API For retrieving a user group
# request : GET
# endpoint : get-user-group
class GetUserGroup(APIView):
    def get(self, request):
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        if user.is_superuser:
            user_groups = user_group.objects.all()
            serializer = UserGroupSerializer(user_groups, many=True)
            return Response({
                'success':True,
                'message': '',
                'data':serializer.data,
            })
        
        else:
            return Response({
                'success':False,
                'message': 'you are not allowed to view User Groups',
                'data':[]
            })


# API For creating user rights
# request : POST
# endpoint : add-user-right
class AddUserRight(APIView):
    def post(self, request):
        payload = verify_token(request)

        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload

        if user.is_superuser:
            temp = request.data
            context = temp.dict()
            context['altered_by'] = user.email
            serializer = UserRightSerializer(data=context)

            if not serializer.is_valid():
                return Response({
                    "success":False,
                    "message": get_error(serializer.errors),
                    "data":{
                        "email":user.email
                    }
                }) 
            
            serializer.save()

            return Response({
                "success": True,
                "message":'User rights added successfully',
                "data":serializer.data  
            })
        
        else:
            return Response({
                "success":False,
                "message":"Not authorized to Add User Rights",
                "data":{
                    "email":user.email
                }
            })

# API For updating user rights
# request : PUT
# endpoint : edit-user-right/<int:id>
class EditUserRight(APIView):
    def put(self, request, id):
        payload = verify_token(request)

        try:
            user = User.objects.filter(id=payload['id'].first())
        except:
            return payload
        
        if user.is_superuser:
            selected_group = user_right.objects.get(id=id)
            temp = request.data
            context = temp.dict()
            context['altered_by'] = user.email
            serializer =  UserRightSerializer(selected_group, data=context)

            if not serializer.is_valid():
                return Response({
                    'success':False,
                    'message':get_error(serializer.errors), 
                })
            
            serializer.save()

            return Response({
                'success':True,
                'message':'User rights edited successfully'
            })
        
        else:
            return Response({
                'success':False,
                'message':'you are not allowed to edit user rights',
            })



# API For deleting user rights
# request : DELETE
# endpoint : delete-user-right/<int:id>
class DeleteUserRight(APIView):
    def delete(self, request, id):
        payload = verify_token(request)

        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        # Permission type : can delete company
        if user.is_superuser:
            # Fetch data using id to delete user right 
            selected_group = user_right.objects.get(id=id)
            selected_group.altered_by = user.email
            selected_group.delete()
            return Response({
                'success': True,
                'message': 'User Right deleted Successfully',
                })
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to Delete User Right',
                })


# API For retrieving a user rights
# request : GET
# endpoint : get-user-right
class GetUserRight(APIView):
    def get(self, request, id):

        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        if user.is_superuser:
            user_group_rights = user_right.objects.filter(user_group_id=id)
            serializer = GetUserRightSerializer(user_group_rights, many=True)
            return Response({
                'success': True,
                'message':'',
                'data':serializer.data
            })
        else:
            return Response({
                'success':False,
                'message': 'You are not allowed to view user right',
                'data':[]
            })

# Logout API
# request : GET
# endpoint : logout
class LogoutView(APIView):

    def get(self, request):
        response = Response()
        # deletes the token
        response.delete_cookie('token')

        response.data=  {
            "success": True, 
            "message": "success",
        }
        return response