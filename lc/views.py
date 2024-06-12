from rest_framework.views import APIView
from rest_framework.response import Response
from .models import lc, lc_docs, lc_amend
from company.models import user_company, user_group
import jwt
from django.http import JsonResponse
from django.http.response import HttpResponse
from .serializers import LCAmendSerializer, GetLCDocsSerializer, LCDocsSerializer, LCSerializer, GetLCSerializer
from company.models import company_master, company_master_docs, year_master
from User.models import User, transaction_right, user_right
import datetime
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
            'success':False,
            'message':"invalid_token",
        }
        payload = JsonResponse(context)

    try:
        payload = jwt.decode(token, 'secret', algorithm=['HS256'])
    except :
        context = {
            'success':False,
            'message':"Invalid_token",
        }
        payload = JsonResponse(context)

    return payload


def get_error(serializerErr):
    err = ''
    for i in serializerErr:
        err = serializerErr[i][0]
        break
    return err


def check_user_company_right(transaction_rights, user_company_id, user_id, need_right):
    try:
        check_transaction_right = transaction_right.objects.filter(transactions=transaction_rights)[0].id
        check_user_group = user_company.objects.get(user=user_id, company_master_id=user_company_id).user_group_id.id
        transaction_right_instance = transaction_right.objects.get(id=check_transaction_right)
        user_group_instance = user_group.objects.get(id=check_user_group)
        check_user_right = user_right.objects.get(user_group_id=user_group_instance, transaction_id=transaction_right_instance)

    except:
        return False
    
    # check condition for user permission
    if need_right=="can_create":
        return check_user_right.can_create
    elif need_right=="can_alter":
        return check_user_right.can_alter
    elif need_right=="can_delete":
        return check_user_right.can_delete
    else:
        return check_user_right.can_view
    



class AddLC(APIView):
    def post(self, request):
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        

        user_permission = check_user_company_right("LC", request.data['company_master_id'], user.id, "can_create")
        if user_permission:
            query_date = datetime.date(int(request.data['lc_date'][:4]), int(request.data['lc_date'][5:7]), int(request.data['lc_date'][8:]))
            year_master_instance = year_master.objects.filter(company_master_id=request.data['company_master_id'])
            year_id = -1
            for i in year_master_instance:
                if i.start_date<=query_date and i.end_date>=query_date:
                    year_id = i.id 

            if year_id == -1:
                return Response({
                    "success":True,
                    "message":"Please choose appropriate date",
                    })
            temp = request.data
            context = temp.dict()
            context['altered_by'] = user.email
            context['year_id'] = year_id
            serializer = LCSerializer(data = context)
            if not serializer.is_valid():
                return Response({
                "success":False,
                "message": get_error(serializer.errors),
                "data": {
                    "email":user.email
                }
                })

            serializer.save()

            return Response({
                "success":True,
                "message":"LC added successfully",
                "data":{
                    "email":user.email
                }
            })
        

class EditLC(APIView):
    def put(self, request, id):
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        user_permission = check_user_company_right("LC", request.data['company_master_id'], user.id, "can_alter")
        if user_permission:
            lc_instance = lc.objects.get(lc_no=id)
            temp = request.data
            context = temp.dict()
            context['altered_by'] = user.email
            serializer = LCSerializer(lc_instance, data=context)

            if not serializer.is_valid():
                print(serializer.errors)
                return Response({
                    'success': False,
                    'message': get_error(serializer.errors),
                    })

            serializer.save()
            return Response({
                'success': True,
                'message': 'LC edited successfully'})
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to edit LC',
                })
        


class Delete(APIView):
    def delete(self, request, id):
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        lc_instance = lc.objects.get(lc_no=id)
        user_permission = check_user_company_right("LC", lc_instance.company_master_id, user.id, "can_delete")
        if user_permission:
            lc_instance.altered_by = user.email
            lc_instance.delete()
            return Response({
                'success': True,
                'message': 'LC deleted Successfully',
                })
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to delete LC',
                })
        

class GetLC(APIView):
    def get(self, request, id):
        payload = verify_token(request)

        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        user_permission = check_user_company_right("LC", id, user.id, "can_view")    
        if user_permission:
            all_lc = lc.objects.filter(company_master_id=id)
            serializer = GetLCSerializer(all_lc, many=True)
            return Response({
            'success': True,
            'message':'',
            'data': serializer.data
            })
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to view LC',
                })
        

class GetDetailLC(APIView):
    def get(self, request, id):
        # verify token
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        lc_instance = lc.objects.get(lc_no=id)
        user_permission = check_user_company_right("LC", lc_instance.company_master_id, user.id, "can_view")
        if user_permission:
           
            serializer = GetLCSerializer(lc_instance)
            return Response({
            'success': True,
            'message':'',
            'data': serializer.data
            })
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to view LC',
                })


class GetImportLC(APIView):
    def get(self, request, id):
        payload = verify_token(request)
        try:
            user = User.objecst.fiter(id=payload['id']).first()
        except:
            return payload
        lc_instance = lc.objects.filter(company_master_id=id, trans_type="import")
        user_permission = check_user_company_right("LC", id, user.id, "can_view")
        if user_permission:
            serializer = GetLCSerializer(lc_instance, many=True)
            return Response({
                'success':True,
                'message':'',
                'data':serializer.data
            })
        else:
            return Response({
                'success':False,
                'message':'you are not allowed to view lc'
            })


class GetExportLC(APIView):
    def get(self, request, id):
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload 
        lc_instance = lc.objects.filter(company_master_id=id, trans_type="export")
        user_permission  =check_user_company_right("LC", id, user.id, "can_view")
        if user_permission:
            serializer = GetLCSerializer(lc_instance, many=True)
            return Response({
                'success':True,
                'message':'',
                'data':serializer.data
            })
        else:
            return Response({
                'success':False,
                'message':'you are not allowed to view lc'
            })
        

class AddLCDoc(APIView):
    def post(seld, request):
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        user_permission = check_user_company_right("LC", request.data['company_master_id'], user.id, "can_create")
        if user_permission:
            temp = request.data
            context = temp.dict()
            context['altered_by'] = user.email
            serializer = LCDocsSerializer(data=context)
            if not serializer.is_valid():
                return Response({
                    "success":False,
                    "message":get_error(serializer.errors),
                    "data":{
                        "email":user.email
                    }
                })
            serializer.save()

            return Response({
                "success":True,
                "message":"LC Document added successfully",
                "data":serializer.data
            })
        
        else:
            return Response({
                "success":False,
                "message":"Not authorized to Add LC Document",
                "data":{
                    "email":user.email
                }
            })
class EditLCDoc(APIView):
    def put(self, request):
        
        payload = verify_token(request)

        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        user_permission = check_user_company_right("LC", request.data['company_master_id'], user.id, "can_alter")
        if user_permission:
            lc_document_instance = lc_docs.objects.get(id=id)
            temp = request.data
            context = temp.dict()
            context['altered_by'] = user.email
            serializer = LCDocsSerializer(lc_document_instance, data=context)

            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'message': get_error(serializer.errors),
                    })
              
            serializer.save()
            
            return Response({
                'success': True,
                'message': 'LC Document Edited successfully'})
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to edit LC Document',
                })


class DeleteLcDoc(APIView):  
    def delete(self, request, id):
        payload = verify_token(request)
        try:
            user = User.objects.filterE(payload['id']).first()
        except:
            return payload
        lc_document = lc_docs.objects.get(id=id)
        lc_instance = lc.objects.get(lc_no=lc_document.lc_id.lc_no)
        user_permission = check_user_company_right("LC", lc_instance.company_master_id, user.id, "can_delete")
        if user_permission:
            lc_document.altered_by = user.email
            lc_document.delete()
            return Response({
                'success': True,
                'message': 'LC Document deleted Successfully',
                })
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to delete LC Document',
                })
        

class GetLcDocuments(APIView):
    def get(self, request, id):
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        lc_instance = lc.objects.get(lc_no=id)
        user_permission = check_user_company_right("LC", lc_instance.company_master_id, user.id, "can_view")
        if user_permission:
            lc_docs_record = lc_docs.objects.filter(lc_id=id)
            serializer = GetLCDocsSerializer(lc_docs_record, many=True)
            return Response({
                'success':True,
                'message':'',
                'data':serializer.data
            })
        else:
            return Response({
                'success':False,
                'message':'you are not allowed to view lc Documnet',
            })
        

class DownloadLcDoc(APIView):
    def get(self, request, id):
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload 
        
        lc_doc = lc_docs.objects.get(id=id)
        user_permission = check_user_company_right("LC", lc_doc.company_master_id, user.id, "can_view")
        if user_permission:
            temp = lc_doc.file 
            im = str(lc_doc.file)
            files = temp.read()
            ext = ""
            im = im[:-1]
            for i in im:
                if i==",":
                    break
                else:
                    ext+=i
            ext = ext[::-1]
            im = im[::-1]
            # print(im)
            file_name = im[6:]
            response = HttpResponse(files, content_type='application/'+ext)
            response['Content-Disposition'] = "attachment; filename="+file_name
            return response    
        



class AddLCAmend(APIView):
    def post(self, request):
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        user_permission = check_user_company_right("LC", request.data['company_master_id'], user.id, "can_create")

        if user_permission:
            lc_instance = lc_amend.objects.filter(lc_id=request.data['lc_id'])
            lc_arr = [0]
            for i in lc_instance:
                lc_arr.append(int(i.amendment_no))
            lc_arr.sort()
            lc_count = lc_arr[-1]+1
            temp = request.data
            context = temp.dict()
            context['altered_by'] = user.email
            context['amendment_no'] = lc_count
            serializer = LCAmendSerializer(data = context)
            if not serializer.is_valid():
                return Response({
                "success":False,
                "message": get_error(serializer.errors),
                "data": {
                    "email":user.email
                }
                })


            serializer.save()

            return Response({
                "success":True,
                "message":"Lc-Amend added successfully",
                "data":serializer.data
                })
        else:
            return Response({
                "success":False,
                "message":"Not authorized to Add LC-Amend",
                "data":{
                    "email":user.email
                }
            })
        

class EditLCAmend(APIView):
    def put(self, request, id):

        payload = verify_token(request)

        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        user_permission = check_user_company_right("LC", request.data['company_master_id'], user.id, "can_alter")
        if user_permission:
            lc_amend_instance = lc_amend.objects.get(id=id)
            temp = request.data
            context = temp.dict()
            context['altered_by'] = user.email
            serializer =LCAmendSerializer(lc_amend_instance, data=context)

            if not serializer.is_valid():
                return Response({
                    'success':False,
                    'message':get_error(serializer.errors),
                })
            
            serializer.save()
            return Response({
                'success': True,
                'message': 'LCAmend edited successfully'})
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to LC Amend',
                })
        

class DeleteLCAmend(APIView):
    def delete(self, request, id):
        payload = verify_token(request)

        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        lc_amend_instance = lc_amend.objects.get(id=id)
        user_permission = check_user_company_right("LC", "can_delete")
        if user_permission:
            lc_amend_instance.altered_by = user.email
            lc_amend_instance.delete()
            return Response({
                'success':True,
                'message': 'LCAmend deleted Successfully',
                })
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to deleteLC Amend',
                })

class GetLCAmend(APIView):
    def get(self, request, id):
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload 
        lc_amend_instance = lc_amend.objects.filter(lc_id=id)
        lc_instance = lc.objects.get(lc_no=id)
        user_permission = check_user_company_right("LC", lc_instance.company_master_id, user.id, "can_view")
        if user_permission:
            serializer = LCAmendSerializer(lc_amend_instance, many=True)
            return Response({
                'success':True,
                'message':'',
                'data':serializer.data
            })
        else:
            return Response({
                'success':True,
                'message':' you are not allowed to view lc amend'
            })
