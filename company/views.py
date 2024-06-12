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
            id request.data['']
        