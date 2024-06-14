from django.db import reset_queries
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import currency, company_master, user_company, company_master_docs, year_master, voucher_type, acc_head, acc_group, ledger_master, cost_category, cost_center, fixed_vouchertype, fixed_account_head, fixed_account_group, fixed_ledger_master, ledger_master_docs
import jwt
from django.http import JsonResponse
from .serializers import CurrencySerializer, CompanySerializer,  GetCompanySerializer, CompanyDocumentSerializer, GetCompanyDocumentSerializer, UserCompanySerializer, GetUserCompanySerializer, GetVoucherTypeSerializer, VoucherTypeSerializer, AccGroupSerializer, GetAccGroupNestedSerializer, GetAccGroupNotNestedSerializer,  AccountHeadSerializer, LedgerMasterSerializer,GetLedgerMasterNotNestedSerializer, GetLedgerMasterNestedSerializer, CostCategorySerializer, GetTransactionSerializer, CostCenterSerializer, GetCostCategorySerializer, GetCostCenterSerializer,GetCostCenterNotNestedSerializer, LedgerDocumentSerializer, YearSerializer
from datetime import date, timedelta
from django.http.response import HttpResponse
from User.models import User, transaction_right, user_group, user_right
from budget.models import budget, budget_details, revised_budget_details
import PIL
import json


def verify_token(request):
    try:
        if not (request.headers['Authorization'] == "null"):
            token = request.headers['Authorization']
    except:
        if not(request.COOKIES.get('token') == "null"):
            token = request.COOKIES.get('token')
        

    else:
        context = {
            "success":False,
            "message":"INVALID_TOKEN"
        }
        payload = JsonResponse(context)


    if not token:
        context= {
            "success":False,
            "message":"INVALID_TOKEN",
        }
        payload = JsonResponse(context)

    try:
        payload = jwt.decode(token, 'secret', algorithm=['HS256'])

    except:
        context = {
            'success':False,
            'message': "Invalid_token",
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
    

    if need_right == "can_create":
        return check_user_right.can_create
    elif need_right == "can_alter":
        return check_user_right.can_alter
    elif need_right == "can_delete":
        return check_user_right.can_delete
    else:
        return check_user_right.can_view
    

class GetTransaction(APIView):
    def get(self, request):
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload 
        
        all_transaction_right = transaction_right.objects.all()

        serializer = GetTransactionSerializer(all_transaction_right, many=True)
        return Response({
            'success':True, 
            'message':'',
            'data':serializer.data
        })
    

class GetUserCompanyView(APIView):
    def get(self, request):
        payload = verify_token(request) 
        try:
            user = User.objects.filter(od=payload['id']).first()
        except:
            return payload
        
        user_company_query = user_company.objects.filter(user=user.id)
        companies=[]
        for i in user_company_query:
            if str(i.company_master_id.logo) == "":
                logo_str = None
            else:
                logo_str = str(i.company_master_id.logo)
            company_year = year_master.objects.filter(company_master_id=i.company_master_id.id).exclude(year_no=0)
            all_year = []
            for j in company_year:
                all_year.append({
                    "year_id":j.id,
                    "start_date":j.start_date,
                    "end_date":j.end_date
                })
            companies.append({"company_id":i.company_master_id.id,"company_name":i.company_master_id.company_name, "country":i.company_master_id.country, "year_start_date": i.company_master_id.year_start_date, "year_end_date": i.company_master_id.year_end_date, "logo": logo_str, "created_on": i.company_master_id.created_on,"base_currency":i.company_master_id.base_currency.id, "years": all_year})

        return Response({
            "success":True, 
            "message":"",
            "data":{
                "user_id":user.id,
                "companies":companies
            }
        })
    


def year_master_insert(year_no,start_date, end_date, company_id, status, locked, user_email):
    new_year_master= year_master(year_no=year_no, start_date=start_date, end_date=end_date, company_master_id=company_id, status=status, locked=locked, created_by=user_email)
    new_year_master.save()


def voucher_type_insert(voucher_name, voucher_class, company_id, user_email):
    for i in range(len(voucher_name)):
        new_voucher_type = voucher_type(voucher_name=voucher_name[i], voucher_class=voucher_class[i], company_master_id = company_id, created_by = user_email)
        new_voucher_type.save()



# Reusable function to insert data into year account head
def acc_head_insert(acc_head_fields, company_id, user_email):
    for i in acc_head_fields:
        new_acc_head = acc_head(acc_head_name=i[0], title=i[1], company_master_id=company_id, bs=i[2],schedule_no=i[3],created_by=user_email )
        new_acc_head.save()


# Reusable function to insert data into year account group
def acc_group_insert(acc_group_fields, company_id, user_email):
    for i in acc_group_fields:
        try:
            new_acc_group = acc_group(group_name=i[0], acc_head_id = i[1], child_of=i[3], group_code=i[2], company_master_id=company_id, created_by=user_email)
            new_acc_group.save()
        except:
            new_acc_group = acc_group(group_name=i[0], acc_head_id = i[1], group_code=i[2], child_of=None, company_master_id=company_id, created_by=user_email)
            new_acc_group.save()


# Reusable function to insert data into year legder master
def ledger_master_insert(ledger_master_fields, company_id, user_email):
    for i in ledger_master_fields:
        new_ledger_master = ledger_master(ledger_id=i[0], ledger_name=i[1], acc_group_id=i[2], maintain_billwise=i[3], company_master_id=company_id, created_by=user_email)
        new_ledger_master.save()


# Reusable function to insert data into user_company
def user_company_insert(user, user_group_id, company_master_id, user_email):
    new_user_company= user_company(user=user, user_group_id=user_group_id, company_master_id=company_master_id, created_by=user_email)
    new_user_company.save()



class CreateCompanyView(APIView):
    def post(self, request):
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        if user.is_superuser:
            if request.data['year_start_date'] > request.data['year_end_date']:
                return Response({
                    'success':False,
                    "message":"year end date should be greater than yeat start date",
                    "data": {
                        "email":user.email
                    }
                })
        
        temp = request.data
        context = temp.dict()
        context ['altered_by'] = user.email
        serializer = CompanySerializer(data = context)
        if not serializer.is_valid():
            return Response({
                "success":False,
                "message":get_error(serializer.errors),
                "data":{
                    "email":user.email
                }
            })
        
        serializer.save()
        added_company = company_master.objects.latest('id')

        company_user_group = user_group.objects.get(user_group_name='ADMIN')

        user_company_insert(user, company_user_group, added_company, user.email)

        diff  = abs(added_company.year_start_date-added_company.year_end_date)
        diff = diff.days
        diff = int(diff)
        year_master_insert(year_no=0,start_date=added_company.year_start_date-timedelta(days=diff+1),end_date=added_company.year_end_date-timedelta(days=diff+1),company_id=added_company,status=False,locked=True,user_email=user.email )
        year_master_insert(year_no=1,start_date=added_company.year_start_date,end_date=added_company.year_end_date,company_id=added_company,status=True,locked=False,user_email=user.email )

        voucher_name = []
        voucher_class = []
        all_fixed_voucher_type = fixed_vouchertype.objects.all()
        for i in all_fixed_voucher_type:
            voucher_name.append(i.voucher_name)
            voucher_class.append(i.vouhcer_class)

        voucher_type_insert(voucher_name, voucher_class, added_company, user.email)


        account_head = []
        all_fixed_account_head = fixed_account_head.objects.all()
        schedule_no=1
        for i in all_fixed_account_head:
            account_head.append([i.acc_head_name, i.title, i.bs, schedule_no])
            schedule_no+=1

        acc_head_insert(account_head, added_company, user.email)

        account_group = []
        all_fixed_account_group = fixed_account_group.objects.all()
        for i in all_fixed_account_group:
            acc_head_instance = acc_head.objects.get(acc_head_name=i.acc_head_id.acc_head_name, company_master_id=added_company.id)
            account_group.append([i.group_name, acc_head_instance  ,i.group_code,i.child_of])


        acc_group_insert(account_group, added_company, user.email)

        ledger_master = []

        all_fixed_ledger_master = fixed_ledger_master.objects.all()

        for i in all_fixed_ledger_master:
            acc_group_instance = acc_group.objects.get(group_name=i.acc_group_id.group_name, company_master_id=added_company.id)
            ledger_master.append([i.ledger_id,i.ledger_name,acc_group_instance,i.maintain_billwise])


            ledger_master_insert(ledger_master, added_company, user.email)

            return Response({
                "success":True, 
                "message":"company created successfully",
                "data":serializer.data
            })
        
        else:
            return Response({
            "success":False,
            "message":"Not Allowed to Create Company",
            "data": {
                    "email":user.email
                }
            })



class EditCompanyView(APIView):
    def put(self, request, id):
        payload = verify_token(request)

        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        if user.is_superuser:
            company_instance = company_master.objects.get(id=id)
            if request.data['year_start_date'] > request.data['year_end_date']:
                return Response({
                    "succes": False,
                    "message":"year end date should be greater than year start date",
                    "data":{
                        "email":user.email
                    }
                })
            temp = request.data
            context = temp.dict()
            context['altered_by'] = user.email
            logo_file = context.get('logo')
            if logo_file!=None and "https://" in logo_file:
                context["logo"] = company_instance.logo
            
            
            serializer = CompanySerializer(company_instance, data=context)
           
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'message': get_error(serializer.errors),
                    })

            # Create Logs Trigger
            serializer.save()
            return Response({
                'success': True,
                'message': 'Company Edited successfully'})
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to edit Company',
                })
        


class DeleteCompanyView(APIView):

    def delete(self, request, id):
        payload = verify_token(request) 

        try:
            user= User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        if user.is_superuser:

            try:
                company_instance = company_master.objects.get(id=id)
                company_instance.altered_by = user.email
                company_instance.delete()

                return Response({
                    'success':True,
                    "message":"company deleted successfully"
                })
            except:
                return Response({
                    "success":False,
                    "message":'please delete all related data this company'
                })
        else:
            return Response({
                'success':False,
                'message': ' you are not allowed to delete company',
            })
        


class DetailCompanyView(APIView):

    def get(self, request, id):
        payload = verify_token(request)

        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        if user.is_superuser:

            company_master_record = company_master.objects.get(id=id)
            serializer = GetCompanySerializer(company_master_record)
            return Response({
                'success':True,
                'message':'',
                'data':serializer.data
            })
        
        else:
            return Response({
                'success':False,
                'message': 'you are not allowed to view company details',
                'data':[]
            })


class CreateUserCompany(APIView):
    def post(self, request):
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        if user.is_superuser:
            temp = request.data
            context = temp.dict()
            context['alterd_by'] = user.email
            serializer = UserCompanySerializer(data=context)
            if not serializer.is_valid():
                return Response({
                    'success':False,
                    "message":get_error(serializer.errors),
                    "data":{
                        "email":user.email
                    }
                })
            
            company_name = company_master.objects.get(id=request.data['company_master_id']).company_name
            serializer.save()
            
            
            return Response({
                "success":True,
                "message":"User has been added to "+company_name+" successfully",
                "data": serializer.data
                })
        else:
            return Response({
            "success":False,
            "message":"Not Allowed to add user",
            "data": {
                    "email":user.email
                }
            })



class EditUserCompany(APIView):
    def put(self, request, id):
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        # check user permission
        if user.is_superuser:
            # print(request.data)
            user_company_instance = user_company.objects.get(id=id)
            temp = request.data
            context = temp.dict()
            context['altered_by'] = user.email
            #request.data.update({'altered_by': user.email})
            serializer = UserCompanySerializer(user_company_instance, data = context)
            if not serializer.is_valid():
                return Response({
                "success":False,
                "message":get_error(serializer.errors),
                "data": {
                    "email":user.email
                } 
                })
            
            serializer.save()
            
            return Response({
                "success":True,
                "message":"User has been edited successfully",
                "data": serializer.data
                })
        else:
            return Response({
            "success":False,
            "message":"Not Allowed to edit user",
            "data": {
                    "email":user.email
                }
            })



class GetUserCompany(APIView):

    def get(self, request):
        payload = verify_token(request)

        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        if user.is_superuser:
            useR_company_query = user_company.objects.filter(user=id)
            serializer = GetUserCompanySerializer(useR_company_query, many=True)
            return Response({
                "success":True,
                "message":"",
                "data":serializer.data
            })
        
        else:
            return Response({
                "success":False,
                "message":"not allowed to view user company",
                "data":{
                    "email":user.email
                }
            })


class DeleteUserCompany(APIView):  
    def delete(self, request, id):
        # verify token for authorization
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload

        # permission : if user can delete company then user can delete company document (Inherited permission)
        if user.is_superuser:

            user_company_instance = user_company.objects.get(id=id)
            company_name = user_company_instance.company_master_id.company_name
            user_company_instance.altered_by = user.email
            user_company_instance.delete()
            return Response({
                'success': True,
                'message': "User from company " + company_name + " has been removed",
                })

        else:
            
            return Response({
                'success': False,
                'message': 'You are not allowed to Delete User Company',
                })



class GetCompanyUser(APIView):
    def get(self, request, id):
        # verify token for authorization
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        user_company_query = user_company.objects.filter(company_master_id=id)
        data1 = []
        for i in user_company_query:
            data = {}
            data.update({"id":i.user.id, "email": i.user.email})
            data1.append(data)
        #serializer = UserCompanySerializer(user_company_query, many=True)
        return Response({
                    "success":True,
                    "message":"",
                    "data": data1
                
                })
    


class AddCompanyDocument(APIView):
    def post(self, request):
        payload = verify_token(request)

        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload

        if user.is_superuser:
            temp = request.data
            context = temp.dict()
            context['alterd_by'] = user.email

            serializer = CompanyDocumentSerializer(data=context)
            if not serializer.is_valid():
                return Response({
                    'success':False,
                    'message': get_error(serializer.errors),
                    'data': {
                        'email': user.email
                    }
                })
            
            else:
                return Response({
                "success":False,
                "message":"Not authorized to Add Company Documents",
                "data":{
                    "email":user.email
                }
            })


class EditCompanyDocumentView(APIView):
    def put(self, request):
        payload = verify_token(request)

        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        if user.is_superuser:
            temp = request.data
            context = temp.dict()
            context['altered_by'] = user.email

            company_document_instance = company_master_docs.objects.get(id=id)
            serializer = CompanyDocumentSerializer(company_document_instance, data=context)

            if not serializer.is_valid():
                return Response({
                    'success':False,
                    'message':get_error(serializer.errors),

                })
            
            serializer.save()
            return Response({
                'success':True,
                'message':'company edited successfully'
            })
        
        else:
            return Response({
                'success':False,
                'message': ' you are not allowed to edit company document'
            })
        



class DeleteCompanyDocument(APIView):
    def delete(self, request, id):
        payload = verify_token(request)

        try:
            user= User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        if user.is_superuser:

            company_master_documents = company_master_docs.objects.get(id=id)
            company_master_documents.altered_by = user.email
            company_master_documents.delete()
            return Response({
                'success': True,
                'message': 'Company Document deleted Successfully',
                })

        else:
            
            return Response({
                'success': False,
                'message': 'You are not allowed to Delete Company Document',
                })


class GetCompanyDocumentView(APIView):
    def get(self, request, id):
        payload = verify_token(request)

        try:
            user = User.objects.filter(id=payload['id']).first()          
        except:
                return payload
        
        if user.is_superuser:
            company_master_docs_record = company_master_docs.objects.filter(company_master_id=id)
            serializer = GetCompanyDocumentSerializer(company_master_docs_record, many=True)
            return Response({
                'success':True, 
                'message':'',
                'data':serializer.data
            })
        else:

            return Response({
                'success': False,
                'message': 'You are not allowed to View Company Document',
                'data': []
            })
        

class DownloadClientDocument(APIView):
    def get(self, request, id):
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()  
        except:
            return payload 
        if user.is_superuser:
            company_document = company_master_docs.objects.get(id=id)
            temp = company_document.file
            im = str(company_document.file)
            
            files = temp.read()
            ext = ""
            im = im[::-1]
            for i in im:
                if i==".":
                    break 
                else:
                    ext += i
            ext = ext[::-1]
            im = im[::-1]
            print(im)
            file_name = im[6:]
            response = HttpResponse(files, content_type='application/'+ext)
            response['Content-Disposition'] = "attachment; filename="+file_name
            return response




class AddCurrency(APIView):
    def post(self, request, id):
        payload = verify_token(request)

        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        if user.is_superuser:
            temp = request.data
            context = temp.dict()
            context['alterd_by'] = user.email
            serializer = CurrencySerializer(data=context)
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
                "message":"Currency added successfully",
                "data":serializer.data
                })
        else:
            return Response({
                "success":False,
                "message":"Not authorized to Add currency",
                "data":{
                    "email":user.email
                }
            })




class EditCurrency(APIView):
    def put(self, request, id):
        payload = verify_token(request)
        try:
            user= User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        if user.is_superuser:
            temp = request.data
            context = temp.dict()
            context['altered_by'] = user.email
            currency_instance = currency.objects.get(id=id)
            serializer = CurrencySerializer(currency_instance, data=context)

            if not serializer.is_valid():
                return Response({
                    'success':False,
                    'message':get_error(serializer.errors),
                })
            
            serializer.save()
            return Response({
                'success':True,
                'message':'currency edited successfully'
            })
        else:
            return Response({
                'success':False,
                'message':'you are not allowed to edit currency',
            })



class DeleteCurrency(APIView):
    def delete(self, request, id):
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        if user.is_superuser:
            currency_instance = currency.objects.get(id=id)
            currency_instance.altered_by = user.email
            currency_instance.delete()
            return Response({
                'success':True, 
                'message':'currency deleted successfully',
            })
        else:
            return Response({
                'success':False,
                'message': ' you are not allowed '
            })


class GetCurrency(APIView):
    def get(self, request):
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        all_currency = currency.objects.all()
        serializer = CurrencySerializer(all_currency, many=True)
        return Response({
            'success':True, 
            'message':'',
            'data':serializer.data
        })



class AddVoucherType(APIView):
    def post(self, request):

        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        

        user_permission = check_user_company_right("Voucher Type", request.data['company_master_id'], user.id, "can_create")

        if user_permission:
            temp = request.data
            context = temp.dict()
            context['altered_by'] = user.email
            #request.data.update({'altered_by': user.email})
            serializer = VoucherTypeSerializer(data = context)
            # validate serialier
            if not serializer.is_valid():
                return Response({
                "success":False,
                "message": get_error(serializer.errors),
                })
            
            serializer.save()
            return Response({
                "success":True,
                "message":"Voucher Type added successfully",
                "data":serializer.data
                })
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to Add Vocher Type',
            })
        



class EditVoucherType(APIView):
    def put(self, request, id):
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        # Query : Getting Voucher Type Instace
        voucher_type_instance = voucher_type.objects.get(id=id)
        temp = request.data
        context = temp.dict()
        context['altered_by'] = user.email
        # request.data.update({'altered_by': user.email})
        serializer = VoucherTypeSerializer(voucher_type_instance, data=context)
        user_permission = check_user_company_right("Voucher Type", request.data['company_master_id'], user.id, "can_alter")
        if user_permission: 
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'message': get_error(serializer.errors),
                    })
            
            serializer.save()
            return Response({
                'success': True,
                'message': 'Voucher Type Edited successfully'})
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to Edit Voucher Type',
            })     



class DeleteVoucherType(APIView):
    def delete(self, request, id):
        # verify token
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        voucher_type_instance = voucher_type.objects.get(id=id)
        # if account head instance is fixed user cannot delete that instance as it is auto trigged at company creation
        if voucher_type_instance.is_fixed:
             return Response({
                'success': False,
                'message': 'You are not allowed to Delete Account Head',
            })
        
        user_permission = check_user_company_right("Voucher Type", voucher_type_instance.company_master_id , user.id, "can_delete")
        if user_permission:  
            # Query : fetch voucher type record using id
            voucher_type_instance = voucher_type.objects.get(id=id)
            voucher_type_instance.altered_by = user.email
            voucher_type_instance.delete()
            return Response({
                'success': True,
                'message': 'Voucher deleted Successfully',
                })
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to Delete Voucher Type',
            })
        


class GetVoucherType(APIView):
    def get(self, request, id):
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload 
        
        user_permission = check_user_company_right("voucher Type", id, user.id, "can_view")
        if user_permission:
            voucher_type_record = voucher_type.objects.filter(company_master_id=id)
            serializer = GetVoucherTypeSerializer(voucher_type_record, many=True)
            return Response({
            'success': True,
            'message':'',
            'data': serializer.data
            })
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to View Voucher Type',
            })    
        



class GetDetailVoucherType(APIView):
    def get(self, request, id):
        payload = verify_token(request)

        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        voucher_type_record = voucher_type.objects.get(id=id)
        user_permission = check_user_company_right("Voucher Type", voucher_type_record.company_master_id, user.id, 'can_view')
        if user_permission:
            serialzier = GetVoucherTypeSerializer(voucher_type_record)
            return Response({
                'success':True, 
                'message':'',
                'data': serialzier.data
                })
        
        else:
            return Response({
                'success':False,
                'message': 'you are not allowed to view voucher type'
            })
        
    


class GetVoucherclass(APIView):
    def get(self, request):
        payload = verify_token(request)

        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        voucher_record = fixed_vouchertype.objects.all()
        data = []
        for i in voucher_record:
            data.append(i.voucher_class)
        return Response({
            'success':True,
            'message':'', 
            'data':data
        })


# ############################################# #


class GetScheduleNo(APIView):
    def get(self, request, id):
        last_comp_schedule_no = acc_head.objects.filter(company_master_id=id)

        sc_no = []
        for i in last_comp_schedule_no:
            sc_no.append(i.schedule_no)
        sc_no.sort()
        return Response({
            'success':True,
            'message':'',
            'data':sc_no
        })



class AddAccountHead(APIView):
    def post(self, request):
        payload = verify_token(request)

        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        user_permission = check_user_company_right('Account head', request.data['company_master_id'], user.id, "can_delete")
        if user_permission:
            temp = request.data
            context = temp.dict()
            context['altered_by'] = user.email
            serializer = AccountHeadSerializer(data=context)
            print(request.data['schedule_no'])
            if not serializer.is_valid():
                print(serializer.errors)
                return Response({
                    'success':False,
                    "message":get_error(serializer.errors),
                })
            

            serializer.save()
            return Response({
                'success':False,
                'message':'you are not allowed to Add Account head'
            })


class EditAccountHead(APIView):
    def put(self, request, id):
        payload= verify_token(request)

        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        acc_head_instance = acc_head.objects.get(id=id)
        
        if acc_head_instance.is_fixed:
            return Response({
                'success':False,
                'message':'you are not allowed to edit acocunt head'
            })
        
        user_permission = check_user_company_right("account head", request.data['comapny_master_id'], user.id, "can_alter")

        if user_permission:
            temp = request.data
            context = temp.dict()
            context['altered_by'] = user.email
            serializer = AccountHeadSerializer(acc_head_instance, data=context)

            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'message': get_error(serializer.errors),
                    })
            serializer.save()
            return Response({
                'success': True,
                'message': 'Account Head Edited successfully'})
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to Add Account Head',
            })



class DeleteAccountHead(APIView):
    def delete(self, request):
        payload = verify_token(request)

        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        acc_head_instance = acc_head.objects.get(id=id)


        if acc_head_instance.is_fixed:
            return Response({
                'success':False,
                'message':'you are not allowed to delete Account head'
            })
        
        user_permission = check_user_company_right("Account Head", acc_head_instance.company_master_id, user.id, "can_delete")
        if user_permission:
            acc_head_instance.altered_by = user.email
            acc_head_instance.delete()
            return Response({
                'success': True,
                'message': 'Account Head deleted Successfully',
                })
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to delete Account Head',
            })
        


class GetAccountHead(APIView):
    def get(self, request, id):
        payload = verify_token(request)

        try:
            user= User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        user_permission = check_user_company_right("Account Head", id, user.id, "can_view")

        if user_permission:
            acc_head_instance = acc_head.objects.filter(company_master_id=id)
            serializer = AccountHeadSerializer(acc_head_instance, many=True)
            return Response({
            'success': True,
            'message':'',
            'data': serializer.data
            })
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to view Account Head',
                'data': []
            })



class AddCostCategory(APIView):
    def post(self, request):
        payload = verify_token(request)

        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        user_permission = check_user_company_right("Cost Category", request.data['company_master_id'], user.id, "can_create")

        if user_permission:
            temp = request.data
            context = temp.dict()
            context['altered_by'] = user.email
            serializer = CostCategorySerializer(data=context)
            if not serializer.is_vlaid():
                return Response({
                    'success':False,
                    'message':get_error(serializer.errors)
                })
            serializer.save()

            return Response({
                'success':True, 
                'message':'cost category added successfully', 
                'data':serializer.data
            })
        
        else:
            return Response({
                "success":False,
                "message":"you are not allowed to add cost category"
            })
        


class EditCostCategory(APIView):
    def put(self, request, id):
        payload = verify_token(request)

        try:
            user=  User.objects.filter(id=payload['id']).first()
        except:
            return Response
        

        user_permission = check_user_company_right("Cost Category", request.data['company_master_id'], user.id, "can_edit")
        if user_permission:
            temp = request.data
            context = temp.dict()
            context['altered_by'] = user.email
            cost_category_instance = cost_category.objects.get(id=id)
            serializer = CostCategorySerializer(cost_category_instance, data=context)

            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'message': get_error(serializer.errors),
                    })

            serializer.save()

            return Response({
                'success': True,
                'message': 'Cost Category Edited successfully'})
        else:
            return Response({
                "success":False,
                "message":"You are not allowed to Edit Cost Category"
                }) 


class DeleteCostCategory(APIView):
    def delete(self, request, id):
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        cost_category_instance = cost_category.objects.get(id=id)
        user_permission = check_user_company_right("Cost Category", cost_category_instance.company_master_id, user.id, "can_delete")
        if user_permission:
            cost_category_instance = cost_category.objects.get(id=id)
            cost_category_instance.altered_by = user.email          
            cost_category_instance.delete()
            return Response({
                'success': True,
                'message': 'Cost Category deleted Successfully',
                })
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to Delete Cost Category',
                })
        



class GetCostCategory(APIView):
    def get(self, request, id):
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
       
        user_permission = check_user_company_right("Cost Category", id , user.id, "can_view")
        if user_permission:
            cost_category_instance = cost_category.objects.filter(company_master_id=id)
            serializer = GetCostCategorySerializer(cost_category_instance, many=True)
            return Response({
            'success': True,
            'message':'',
            'data':  serializer.data
            
            })
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to View Cost Categories',
                'data': []
            })
        
        
# Account Group (CRUD) 

class AddAccGroup(APIView):
    def post (self, request):
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        user_permission = check_user_company_right("Account Group", request.data['company_master_id'], user.id, "can_create")
        if user_permission:
            temp = request.data
            context = temp.dict()
            context['altered_by'] = user.email
            serializer = AccGroupSerializer(data=context)
            if not serializer.is_valid():
                return Response({
                    'success':False,
                    'message':get_error(serializer.errors),
                }) 
            
            serializer.save()

            return Response({
                'success':True, 
                "message":"account group added successfully", 
                'data':serializer.data
            })
        
        else:
            return Response({
                'success':False, 
                'message':'you are not allowed to end Account group'
            })
        




class EditAccGroup(APIView):
    def put(self, request, id):
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        

        accgroup_instance = acc_group.objects.get(id=id)
        if(accgroup_instance.is_fixed):
            return Response({
            'success': False,
            'message': 'You cannot edit Account group',
            })
        user_permission = check_user_company_right("Account Group", request.data['company_master_id'], user.id, "can_alter")


        if user_permission:
            temp = request.data
            context = temp.dict()
            context['altered_by'] = user.email
            #request.data.update({'altered_by': user.email})
            serializer = AccGroupSerializer(accgroup_instance, data=context)
            
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'message': get_error(serializer.errors),
                    })
            
            serializer.save()
            return Response({
                'success': True,
                'message': 'Account Group Edited successfully'})
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to edit Account group',
                }) 


    

class DeleteAccGroup(APIView):
    def delete(self, request, id):
        payload = verify_token(request)

        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        accgroup_instance = acc_group.objects.get(id=id)
        if (accgroup_instance.is_fixed):
            return Response({
                'success':False,
                'message':'you cannot delete this field'
            })
        
        user_permission = check_user_company_right("Account Group", accgroup_instance.company_master_id, user.id, "can_delete")
        if user_permission:
            accgroup_instance.altered_by = user.email
            accgroup_instance.delete()
            return Response({
                'success': True,
                'message': 'Account group deleted Successfully',
                })
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to delete Account Group',
                }) 
        


class GetDetailAccGroup(APIView):
    def egt(self, request, id):
        payload = verify_token(request)

        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        acc_group_record = acc_group.objects.get(id=id)
        user_permission = check_user_company_right("Account Group", acc_group_record.company_master_id, user.id, "can_view")

        if user_permission:
            serializer = GetAccGroupNestedSerializer(acc_group_record)
            return Response({
                'success':True, 
                'message':'', 
                'data':serializer.data
            })
        else:
            return Response({
                'success':False,
                'message':'you are not allowed to view Account group',
                'data': []
            })
        

class GetAccGroupName(APIView):
    def get(self, request, id):
        payload = verify_token(request)

        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        company_instance = acc_head.objects.get(id=id).company_master_id
        
        user_permission = check_user_company_right("Account Group", company_instance.id, user.id, "can_view")
        if user_permission:
            acc_group_record = acc_group.objects.filter(acc_head_id=id)
            grp_name = []
            for i in acc_group_record:
                grp_name.append({'id':i.id, 'group_name':i. group_name})
            return Response({
            'success': True,
            'message':'',
            'data': grp_name
            })
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to view Account group name',
                'data': []
                }) 
        

class GetAccGroup(APIView):
    def get(self, request, id):
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        # id is acc head id
        user_permission = check_user_company_right("Account Group",id, user.id, "can_view")
        if user_permission:
            acc_group_record = acc_group.objects.filter(company_master_id=id)
            serializer = GetAccGroupNotNestedSerializer(acc_group_record, many=True)
            return Response({
            'success': True,
            'message':'',
            'data': serializer.data
            })
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to view Account group name',
                'data': []
                }) 


#### Account LEDGER (CRUD) 


class AddLedgerMaster(APIView):
    def pot(self, request):
        payload = verify_token(request)

        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        user_permission = check_user_company_right("Ledger Master", request.data['company_master_id'], user.id, "can_create")

        if user_permission:
            group_code = acc_group.objects.get(id=request.data['acc_group_id']).group_code
            all_ledger_master = ledger_master.objects.filter(company_master_id=request.data['company_master_id']).count() + 1
            new_ledger_id = str(group_code) + "-" + str(all_ledger_master)

            temp = request.data
            context = temp.dict()

            context['alterd_by'] = user.email
            context['ledger_id'] = new_ledger_id
            serializer = LedgerMasterSerializer(data= context)

            if not serializer.is_valid():
                return Response({
                    'success':False,
                    'message':get_error(serializer.errors)
                })
            
            serializer.save()

            latest_ledger = ledger_master.objects.latest('id')
            if latest_ledger.acc_group_id.acc_head_id.bs==False:
                all_budget = budget.objects.filter(company_master_id=latest_ledger.company_master_id, budget_type="P&L").values('id')

                for i in all_budget:
                    new_budget_details = budget_details(budget_id_id=i['id'],
                    company_master_id_id=latest_ledger.company_master_id.id,ledger_id_id = latest_ledger.id,
                    jan=0,feb=0,mar=0,apr=0,may=0,jun=0,jul=0,aug=0,sep=0,octo=0,nov=0,dec=0,created_by=user.email)
                    new_budget_details.save()
                    new_rev_budget_details = revised_budget_details(budget_id_id=i['id'],company_master_id_id=latest_ledger.company_master_id.id, ledger_id_id = latest_ledger.id,
                    jan=0,feb=0,mar=0,apr=0,may=0,jun=0,jul=0,aug=0,sep=0,octo=0,nov=0,dec=0,created_by=user.email)
                    new_rev_budget_details.save()

            return Response({
                'success':False, 
                'message':"ledger master added successfully", 
                "data": serializer.data
            })
        
        else:
            return Response({
                'success':False,
                'message': ' you are not allowed to add ledger master ', 
            })



class EditLedgerMaster(APIView):
    def put(self, request, id):
        payload = verify_token(request)

        try:
            user = User.objects.filter(id=payload['id']).firsT()
        except:
            return payload  
        
        user_permission = check_user_company_right("Ledger Master", request.data['company_master_id'], user.id, "can_edit")
        ledger_master_instance = ledger_master.objects.get(id=id)

        if (ledger_master_instance.is_fixed):
            return Response({
                'success':False,
                'message': ' you cannot edit this field '
            })
        
        if user_permission:
            temp = request.data
            context = temp.dict()
            context ['altered_by'] = user.email

            serializer = LedgerMasterSerializer(ledger_master_instance, data=context)

            if not serializer.is_valid():
                return Response({
                    'success':False, 
                    'message':get_error(serializer.errors)
                })
            
            serializer.save()
            return Response({
                'success': True,
                'message': 'Ledger Master edited successfully'})
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to edit this field',
                }) 





class DeleteLedgerMaster(APIView):
    def deelte(self, request, id):

        payload = verify_token(request)

        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        ledger_master_instance = ledger_master.objects.get(id=id)

        if (ledger_master_instance.is_fixed):
            return Response({
                'success':False, 
                'message':'you cannot delete this field'
            })
        
        user_permission = check_user_company_right("Ledger Master", ledger_master_instance.company_master_id, user.id, "can_delete")

        if user_permission:
            ledger_master_instance.altered_by = user.email
            ledger_master_instance.delete()
            return Response({
                'success':True, 
                'message':'ledger master deleted successfully '

            })
        else:
            return Response({
                'success':False, 
                'message':'you are not allowed to delete ledger master', 
            })

class GetLedgerMaster(APIView):
    def getr(self, request, id):
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        user_permission = check_user_company_right("ledger Master", id, user.id, 'can_view')

        if user_permission:
            ledger_master_record = ledger_master.objects.filter(company_master_id=id)
            serializer = GetLedgerMasterNotNestedSerializer(ledger_master_record, many=True)
            return Response({
            'success': True,
            'message':'',
            'data': serializer.data
            })
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to view Ledger master',
                'data': []
                }) 
        


class GetDetailLedgerMaster(APIView):
    def get(self, request):
        payload = verify_token(request)

        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return Response
        
        ledger_master_record = ledger_master.objects.get(id=id)

        user_permission = check_user_company_right("Ledger Master", ledger_master_record.company_master_id, user.id, "can_view")

        if user_permission:
            serializer = GetLedgerMasterNestedSerializer(ledger_master_record)
            return Response({
            'success': True,
            'message':'',
            'data': serializer.data
            })
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to view Ledger master',
                'data': []
                })



class GetAccLedgerMaster(APIView):
    def get(self, request):
        payload = verify_token(request)

        try:
            user = User.objects.filter(i=payload['id']).first()
        except:
            return payload
        
        all_receivables = acc_group.objects.get(group_name="Receivables", company_master_id=id)
        all_payables = acc_group.objects.get(group_name="Payables", company_master_id=id)

        all_acc_grp =  acc_group.objects.filter(company_master_id=id)
        acc_grp = []
        for i in all_acc_grp:
            d = {}

            if(i.id==all_receivables.id or str(i.child_of)==str(all_receivables.group_name)):
                d["id"] = i.id
                d["group_name"] = i.group_name
                d["is_Receivables"] = True
                d["is_payables"] = False
                d["is_bs"] = i.acc_head_id.bs
                acc_grp.append(d)
            elif(i.id==all_payables.id or str(i.child_of)==str(all_payables.group_name)):
                d["id"] = i.id
                d["group_name"] = i.group_name
                d["is_Receivables"] = False
                d["is_payables"] = True
                d["is_bs"] = i. acc_head_id.bs
                acc_grp.append(d)
            else:
                d["id"] = i.id
                d["group_name"] = i.group_name
                d["is_Receivables"] = False
                d["is_payables"] = False
                d["is_bs"] = i.acc_head_id.bs
                acc_grp.append(d)

        
        return Response({
                'success': True,
                'message': '',
                'data': acc_grp
                })



class GetLedgerRecievables(APIView):
    def get(self, request, id):
        payload = verify_token(request)

        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        ledger = []

        all_ledger_master = ledger_master.objects.filter(company_master_id=id)
        #rec_acc_group = acc_group.objects.get(group_name="Receivables", company_master_id=id)
        for instance in all_ledger_master:
           
           
            if instance.acc_group_id.group_name == "Receivables" or str(instance.acc_group_id.child_of) == "Receivables":
                ledger.append({'id':instance.id,'ledger_name':instance.ledger_name, "ledger_id": instance.ledger_id})
        
        return Response({
            'success': True,
            'message':'',
            'data':ledger
        })
    

class GetLedgerPayables(APIView):
    def get(self, request, id):
        payload = verify_token(request)

        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload 
        
        ledgers = []

        all_ledger_master = ledger_master.objects.filter(company_master_id=id)

        for instance in all_ledger_master:

            if instance.acc_group_id.group_name == "Payables" or str(instance.acc_group_id.child_of) == "Payables":
                ledgers.append({'id':instance.id,'ledger_name':instance.ledger_name, "ledger_id": instance.ledger_id})
        
        return Response({
            'success': True,
            'message':'',
            'data':ledgers
        })


class GetLedgerCashBank(APIView):
    def GEt(self, request, id):
        payload = verify_token(request)

        try:
            use = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        ledgers = []

        all_ledger_master = ledger_master.objects.filter(company_master_id=id)

        for instance in all_ledger_master:

            if instance.acc_group_id.group_name == "Bank OD" or str(instance.acc_group_id.child_of) == "Bank OD" or instance.acc_group_id.group_name == "Cash at Bank" or str(instance.acc_group_id.child_of) == "Cash at Bank":
                ledgers.append({'id':instance.id,'ledger_name':instance.ledger_name, "ledger_id": instance.ledger_id})
        
        return Response({
            'success': True,
            'message':'',
            'data':ledgers
        })
    
# LEDGER MASTER DOCUMENT (CRUD) 


class AddLedgerDocument(APIView):
    def psot(self, request):
        payload = verify_token(request)

        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        user_permission = check_user_company_right("Ledger Master", request.data['company_master_id'], user.id, "can_create")
        if user_permission:
            temp = request.data
            context = temp.dict()
            context['altered_by'] = user.email
            serializer = LedgerDocumentSerializer(data = context)

            if not serializer.is_valid():
                return Response({
                    'success':False, 
                    'message':get_error(serializer.errors), 
                    'data':{
                        'email':user.email
                    }
                }) 
            
            serializer.save()
            return Response({
                "success":True,
                "message":"Ledger Document added successfully",
                "data":serializer.data
                })
        else:
            return Response({
                "success":False,
                "message":"Not authorized to Add Ledger Documents",
                "data":{
                    "email":user.email
                }
            })



class EditLedgerDocument(APIView):

    def put(self, request, id):
        payload = verify_token(request)

        try:
            user = User.objects.filter(id=payload['id']).fist()
        except:
            return payload 
        
        user_permission = check_user_company_right("Ledger Master", request.data['company_master_id'], user.id, "can_edit")
        ledger_master_doc_instance = ledger_master_docs.objects.get(id=id)
        if user_permission:
            temp = request.data
            context = temp.dict()
            context['altered_by'] = user.email
            
            serializer = LedgerDocumentSerializer(ledger_master_doc_instance, data=context)

            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'message': get_error(serializer.errors),
                    })
           
            serializer.save()
            return Response({
                'success': True,
                'message': 'Ledger document Edited successfully'})
                
        else:
            
            return Response({
                'success': False,
                'message': 'You are not allowed to edit ledger Document',
                })

class DeleteLedgerDocument(APIView):
    def deletE(self, request, id):
        payload = verify_token(request)

        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        ledger_master_doc_instance = ledger_master_docs.objects.get(id=id)
        ledger_master_instance = ledger_master.objects.get(id=ledger_master_doc_instance.ledger_master_id.id)

        if(ledger_master_instance.is_fixed):
            return Response({
            'success': False,
            'message': 'You cannot delete this field',
            })
        user_permission = check_user_company_right("Ledger Master", ledger_master_doc_instance.company_master_id, user.id, "can_delete")
        if user_permission:
            ledger_master_doc_instance.altered_by = user.email
            ledger_master_doc_instance.delete()
            return Response({
                'success': True,
                'message': 'Ledger Document deleted Successfully',
                })
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to delete this Ledger Document',
                }) 



class GetLedgerDocument(APIView):
    def get(self, request, id):
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload

        ledger_master_record = ledger_master.objects.get(id=id)

        user_permission = check_user_company_right("Ledger Master", ledger_master_record.company_master_id, user.id, "can_view")
        if user_permission:
            ledger_document_instance = ledger_master_docs.objects.filter(ledger_master_id=id, company_master_id=ledger_master_record.company_master_id)
            serializer = LedgerDocumentSerializer(ledger_document_instance, many=True)
            return Response({
            'success': True,
            'message':'',
            'data': serializer.data
            })
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to view Ledger master document',
                'data': []
                })  


class DownloadLedgerDocument(APIView):
    def get(self, request, id):
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()  
        except:
            return payload
        ledger_document = ledger_master_docs.objects.get(id=id) 
        user_permission = check_user_company_right("Ledger Master", ledger_document.company_master_id, user.id, "can_view")
        if user_permission:
     
            temp = ledger_document.file
            im = str(ledger_document.file)
            
            files = temp.read()
            ext = ""
            im = im[::-1]
            for i in im:
                if i==".":
                    break 
                else:
                    ext += i
            ext = ext[::-1]
            im = im[::-1]
            print(im)
            file_name = im[6:]
            response = HttpResponse(files, content_type='application/'+ext)
            response['Content-Disposition'] = "attachment; filename="+file_name
            return response
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to download ledger Document',
              
            })

## Cost Center (CRUD) 


class AddCostCenter(APIView):
    def psot(self, request):
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        user_permission = check_user_company_right("Cost center", request.data['company_master_id'], user.id, "can_create")
        if user_permission:
            temp = request.data
            context = temp.dict()
            context['altered_by'] = user.email
            # request.data.update({'altered_by': user.email})
            serializer = CostCenterSerializer(data = context)
            if not serializer.is_valid():
                return Response({
                "success":False,
                "message": get_error(serializer.errors),
                })
    
            serializer.save()
            return Response({
                "success":True,
                "message":"Cost Center added successfully",
                "data":serializer.data
                })
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to Add Cost Center',
                })



class EditCostCenter(APIView):
    def put(self, request, id):
        payload = verify_token(request)
        try:
            user = User.objects.filter(id= payload['id']).first()
        except:
            return payload 
        

        cost_center_instance = cost_center.objects.get(id=id)
        user_permission = check_user_company_right("Cost center", request.data['company_master_id'], user.id, "can_alter")
        if user_permission:
            temp = request.data
            context = temp.dict()
            context['altered_by'] = user.email

            serializer = CostCenterSerializer(cost_center_instance, data=context)

            if not serializer.is_valid():
                return Response({
                    'success':False, 
                    'message':get_error(serializer.errors), 
                })
            
            serializer.save()
            return Response({
                'success':True, 
               'message':'cost center edited successfully' 
            })
        
        else:
            return Response({
                'success':False, 
                'message': 'you are not allowed to edit cost center'
            })
        


class DeleteCostCenter(APIView):
    def delete(self, request, id):
        payload = verify_token(request)

        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload 
        cost_center_instance = cost_center.objects.get(id=id)
        user_permission = check_user_company_right("Cost center", cost_center_instance.company_master_id, user.id, "can_delete")

        if user_permission:
            cost_center_instance.altered_by = user.email
            cost_center_instance.delete()
            return Response({
                'success':True, 
                'message': 'You are not allowed to delete Cost Center',
                }) 


class GetDetailCostCenter(APIView):
    def get(self, request, id):
        payload = verify_token(request)

        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        cost_center_record = cost_center.objects.get(id=id)
        user_permission = check_user_company_right("Cost center", cost_center_record.company_master_id, user.id, "can_view")

        if user_permission:
            serializer = GetCostCenterSerializer(cost_center_record)
            return Response({
            'success': True,
            'message':'',
            'data': serializer.data
            })
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to view cost center',
                'data': []
                }) 




class GetCostCenterName(APIView):
    def get(self, request, id):
        payload = verify_token(request)

        try:
            user = User.objects.filter(id=payload['id']).first() 
        except:
            return payload
        
        company_instance = cost_category.objects.get(id=id).company_master_id

        user_permission = check_user_company_right("Cost center", company_instance.id, user.id, "can_view")

        if user_permission:
            cost_center_record = cost_center.objects.filter(cost_category_id=id)
            cost_center_names=[]
            for i in cost_center_record:
                cost_center_names.append({'id':i.id, 'cost_center_name':i. cost_center_name})
            return Response({
            'success': True,
            'message':'',
            'data': cost_center_names
            })
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to view Cost Center Names',
                'data': []
                }) 




class GetCostCenter(APIView):
    def get(self, request, id):
        payload = verify_token(request)

        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload 
        
        user_permission = check_user_company_right("Cost center",id, user.id, "can_view")
        if user_permission:

            cost_center_record = cost_center.objects.filter(company_master_id=id)
            serializer = GetCostCenterNotNestedSerializer(cost_center_record, many=True)
            return Response({
            'success': True,
            'message':'',
            'data': serializer.data
            })
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to view Account group name',
                'data': []
                }) 
        
## Year Master (CRUD) 

class GetYearMaster(APIView):
    def get(self, request):
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        year_master_record = year_master.objects.filter(company_master_id=id).exclude(year_no="0")

        serializer = YearSerializer(year_master_record, many=True)
        return Response({
            'success':True, 
            'message':'', 
            'data':serializer.data
        })