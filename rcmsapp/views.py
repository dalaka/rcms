from statistics import mode

from django.db import models
from django.db.models.functions import Cast
from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
from django.utils.timezone import now

import datetime
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import pandas as pd

from rcmsapp.models import User, Company, Transaction, Config, Item, Report
from rcmsapp.serializer import UserSerializer, createuser, ChangePasswordSerializer, CompanySerializer, TranxSerializer, \
    ConfigSerializer, ItemSerializer, ReportSerializer
from django.db.models import Q, F


def benchmark1(data, period,name,tin):
    m={}
    m_list = []
    pay = []
    freq=[]
    a=0
    for p in period:
        res = data.filter(month=p)
        if res.exists():
            for i in res:
                pay.append(i.amount_paid)
                a +=1
            freq.append(a)
        m[p]=a

    m_list.append(m)





    if len(pay)==0 or len(freq)==0:
        paymode= 0
        mode2 = 0
    else:
        paymode = mode(pay)
        mode2 = mode(freq)

    if sum(pay) ==0:
        benchmark_2 = 0
    else:
        benchmark_2 = (sum(pay)*mode2)/sum(freq)
    total_expected = max(paymode, benchmark_2)*len(period)
    monthly_expected = max(paymode, benchmark_2)
    outstanding = total_expected - sum(pay)
    config = Config.objects.get(name='PAYE')
    penalty = (config.penalty/100) * abs(outstanding)
    interest = (config.interest/100) * abs(outstanding)
    grand_total = round(penalty,2) + round(interest,2) + abs(outstanding)
    if outstanding <=0 or monthly_expected <=0:
        month_defaulted = 0
    else:
        month_defaulted = outstanding/monthly_expected
    if month_defaulted ==0 and sum(pay) > 0:
        status= "Complied"
    elif month_defaulted >0:
        status="Has Outstanding"
    else:
        status ="Not-Complied"
    result = {"months":m_list,"Status":status, "month_defaulted":round(month_defaulted,1),"outstanding":round(outstanding,2),"monthly_expected":round(monthly_expected,2),"total_expected":round(total_expected,2),"TIN":tin,"payer":name,"benchmark_1": paymode, "benchmark_2":benchmark_2,"total_actual": sum(pay),\
              "frequent_entry":mode2,"total_entry":sum(freq),"interest":round(interest,2), "penalty": round(penalty,2), "grand_total_liability": round(abs(grand_total),2)}

    return result

def final(data):
    total_liability =0
    complied = 0
    defaulted = 0
    for i in data:
        total_liability +=i["grand_total_liability"]
        if i["Status"] =="Complied":
            complied +=1
        else:
            defaulted +=1

    return {"total_liability":round(total_liability,2), "total_complied":round(complied,2), "total_defaulted":round(defaulted)}




class UserView(viewsets.ModelViewSet):
    """PAYE endpoints"""
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get_queryset(self):
        obj = User.objects.all()
        return obj

    def create(self, request, *args, **kwargs):

        usr=User.objects.filter(username=request.data['username'])
        if usr.exists() ==True:
            return Response({
                    "status": "failed",
                    "responsecode": "01",
                    "message": "username address has already been registered",
                    "data": []
                }, status=status.HTTP_401_UNAUTHORIZED)

        else:
            res=createuser(request.data)
            serialiseduser=UserSerializer(res)
            return Response({
                            "status": "success",
                            "responsecode": "00",
                            "message": "New user has been created successfully, check your device for otp to activate your account",
                            "data": serialiseduser.data
                            }, status=200)

    def update(self, request, *args, **kwargs):
        user_object = self.get_object()
        user_object.email = request.data.get('email', user_object.email)
        user_object.first_name = request.data.get("first_name", user_object.first_name)
        user_object.last_name = request.data.get("last_name",user_object.last_name)
        user_object.is_active =request.data.get("is_active",user_object.is_active)
        user_object.role = request.data.get("role", user_object.role)
        user_object.modified_at = now()
        user_object.save()
        serializer = UserSerializer(user_object)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        user= self.get_object()

        if user:
            user.delete()
            return Response({"message":"The user deleted successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "User not found"}, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordView(generics.UpdateAPIView):
    queryset = User.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = ChangePasswordSerializer


class CompanyViews(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = CompanySerializer

    def get_queryset(self):
        return Company.objects.all()

    def create(self, request, *args, **kwargs):

        try:
            file = request.data.get('file')
            reader = pd.read_csv(file)
            reader= reader.fillna('')
            #reader.astype({'TIN': 'int'})
            reader['tin']=reader['tin'].astype('int64')
            print(reader)
            company_list=[]

            for _, row in reader.iterrows():
                company= Company.objects.filter(tin=row['tin']).exists()
                if company==True:
                    company_list.append(dict(row))
            if len(company_list) >0:
                return Response({"status": "Company already existed in the database", "data": company_list}, status.HTTP_403_FORBIDDEN)

            for _, row in reader.iterrows():
                company_list.append(dict(row))
            res = CompanySerializer.create(self,company_list)
            if res:

                return  Response({"status": "Data has been uploaded successfully", "data":company_list}, status.HTTP_201_CREATED)


        except:
            raise APIException("Invalid request data supplied, request data")

    def destroy(self, request, *args, **kwargs):
        org = self.get_object()

        if org:
            org.delete()
            return Response({"message":"The Company deleted successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Company not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['DELETE'])
    def bulk_delete(self, request, *args, **kwargs):
        delete_confirm =request.query_params.get('confirm', None)
        if delete_confirm != 'delete all':
            return Response({"message": "You must confirm by typing delete all"}, status=status.HTTP_400_BAD_REQUEST)
        res=Company.objects.all().delete()
        if res:
            return Response({"message":"The Company data deleted successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Company not found"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['GET'])
    def company_detail(self, request, *args, **kwargs):
        tin =request.query_params.get('tin', None)
        start = request.query_params.get('start_date', None)
        end =request.query_params.get('end_date', None)
        company_detail= Report.objects.filter(start=start,end=end)
        if company_detail.exists():
            ress =[y for y in company_detail[0].data["defined"] if y["TIN"]==tin]

            return Response({"message": "Company details", "data":ress}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Company details not found", "data": []}, status=status.HTTP_200_OK)

class TranxViews(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = TranxSerializer
    def get_queryset(self):
        return Transaction.objects.all()

    def create(self, request, *args, **kwargs):

        year=  request.query_params.get('year', None)
        month = request.query_params.get('month', None)
        tax_item = request.query_params.get('tax_item', None)
        try:
            file = request.data.get('file')
            reader = pd.read_csv(file,skipinitialspace = True)
            reader.taxpayer_name.str.strip()
            reader= reader.fillna('')
            reader['tin'] = reader['tin'].astype('int64')
            tranx_list=[]
            tranx= Transaction.objects.filter(year=year, month=month).exists()
            if tranx==True:
                return Response({"status": "Transaction already existed in the database", "data": []}, status.HTTP_403_FORBIDDEN)

            for _, row in reader.iterrows():
                tranx_list.append(dict(row))
            res = TranxSerializer.create(self,tranx_list, year, month,tax_item)



            return  Response({"status": "Data has been uploaded successfully", "data":tranx_list}, status.HTTP_201_CREATED)


        except:
            raise APIException("Invalid request data supplied, request data")

    @action(detail=False, methods=['DELETE'])
    def bulk_delete(self, request, *args, **kwargs):
        month =request.query_params.get('month', None)
        year =request.query_params.get('year', None)
        tax_item = request.query_params.get('tax_item', None)

        if month == None or year==None:
            return Response({"message": "You must write the right date"}, status=status.HTTP_400_BAD_REQUEST)
        res=Transaction.objects.filter(month=month,year=year,tax_item=tax_item).delete()
        if res:
            return Response({"message":"The transaction data deleted successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "transaction not found"}, status=status.HTTP_400_BAD_REQUEST)



class ReportViews(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = ReportSerializer

    def get_queryset(self):
        return Report.objects.all()

    def create(self, request, *args, **kwargs):


        tax_item = request.query_params.get('item_id', None)
        item_object = Item.objects.get(id = tax_item)
        start_date = request.query_params.get('start_date', None)
        dt = datetime.datetime.strptime(start_date, '%Y-%m')
        end_date = request.query_params.get('end_date', None)
        month_list = pd.period_range(start=start_date, end=end_date, freq='M')
        month_list = [month.strftime("%m") for month in month_list]
        pay_load = []
        undefined = []

        #date=request.query_params.get('date', None)
        if Transaction.objects.filter(year=dt.year, tax_item =item_object.name).exists() == False:
            return  Response({"message":"No transaction data"}, status=status.HTTP_404_NOT_FOUND)
        payers = Company.objects.all()
        for payer in payers:
            res= Transaction.objects.filter(taxpayer_name__contains=payer.name, tax_item__contains=item_object.name, year=str(dt.year))
            result = benchmark1(res,month_list,payer.name,payer.tin)
            if result["total_actual"] <= 0:
                undefined.append(result)
            else:
                pay_load.append(result)

        finals = final(pay_load)
        data={"defined":pay_load, "undefined":undefined}
        if Report.objects.filter(item_id=tax_item, year=dt.year).exists():
            new =Report.objects.get(year=dt.year, item_id=tax_item)
            new.start=start_date
            new.end = end_date
            new.total_compiled_organisaction=finals["total_complied"]
            new.total_defaulted_organisaction =finals["total_defaulted"]
            new.total_liability=finals["total_liability"]
            new.data = data
            new.save()

            trnx= ReportSerializer(new)
            return Response({"message": "report", "data": trnx.data}, status=status.HTTP_200_OK)
        else:
            ress=Report.objects.create(start=start_date,year=dt.year,end=end_date,item_id=tax_item,total_compiled_organisaction=finals["total_complied"], total_defaulted_organisaction=finals["total_defaulted"],total_liability=finals["total_liability"],data=data)


            trnx= ReportSerializer(ress)
            return Response({"message": "report", "data": trnx.data}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['DELETE'])
    def bulk_delete(self, request, *args, **kwargs):
        start =request.query_params.get('start_date', None)
        end =request.query_params.get('end_date', None)
        tax_item = request.query_params.get('item_id', None)

        if start == None or end==None:
            return Response({"message": "You must write the right date"}, status=status.HTTP_400_BAD_REQUEST)
        res=Report.objects.filter(start=start,end=end,item_id__id=tax_item).delete()
        if res:
            return Response({"message":"The report data deleted successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Report not found"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['GET'])
    def dashboard_stat(self, request, *args, **kwargs):
        year = request.query_params.get('year', None)
        data = []

        defl =0
        compls = 0
        liability=0
        total_gen =0
        total_lib =0
        ress=None
        report= Report.objects.filter(year=year, item_id=1)
        if report.exists():
            dt=report[0]
            month_list = pd.period_range(start=dt.start, end=dt.end, freq='M')
            month_list = [month.strftime("%m") for month in month_list]
            total_complied_org=dt.total_compiled_organisaction
            total_defaulted_org = dt.total_defaulted_organisaction
            total_lib = dt.total_liability
            res=dt.data["defined"]
            for i in month_list:
                for d in res:
                    total_gen += d["total_actual"]
                    f=d["months"][0]
                    if f[i]>0:
                        compls+=1
                    else:
                        defl +=1
                        liability += d["grand_total_liability"]

                ress = {"month":i, "complied_org": compls, "default_org": defl, "total_liability":liability}
                liability =0
                defl=0
                compls=0
                data.append(ress)
            r_dict= {"total_complied_org":total_complied_org,"total_defaulted_org": total_defaulted_org,"total_liability":total_lib, "total_generated":round(total_gen,2), "data":data }

            return Response({"message": "dashboard", "result":r_dict}, status=status.HTTP_200_OK)
        else:
            r_dict = {"total_complied_org": 0, "total_defaulted_org": 0,"total_liability": 0, "total_generated":0, "data": []}
            return Response({"message": "No records", "result": r_dict}, status=status.HTTP_200_OK)

class ConfigViews(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = ConfigSerializer

    def get_queryset(self):
        obj = Config.objects.all()
        return obj

    def update(self, request, *args, **kwargs):
        config=self.get_object()
        config.penalty=request.data.get('penalty', config.penalty)
        config.interest=request.data.get('interest', config.interest)
        config.save()
        res = ConfigSerializer(config)
        return Response({"message": "updated successfullyt", "data": res.data}, status=status.HTTP_200_OK)





    @action(detail=False, methods=['GET'])
    def date_data(self, request, *args, **kwargs):
        current_year = datetime.datetime.now().date().year
        months = range(1, 13)
        a = (int(current_year) + 1) - 5
        years = range(a, int(current_year) + 1)
        month_list = ['0' + str(month) if month < 10 else str(month) for month in months]
        year_list = [str(year) for year in years]

        data = {"year": year_list, "month": month_list}

        return Response({"message": "dates", "data": data}, status=status.HTTP_200_OK)


class ItemViews(viewsets.ModelViewSet):
    # permission_classes = (IsAuthenticated,)
    serializer_class = ItemSerializer

    def get_queryset(self):
        obj = Item.objects.all()
        return obj
    def create(self, request, *args, **kwargs):

        item = request.data
        if item is not None:
            if Item.objects.filter(name=item["name"]).exists():
                return Response({"message": "Item already exists", "data": []}, status=status.HTTP_400_BAD_REQUEST)
            else:
                res = Item.objects.create(name=item["name"])
                data= ItemSerializer(res)
                return Response({"message": "created successfully", "data": data.data}, status=status.HTTP_201_CREATED)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)



    def update(self, request, *args, **kwargs):
        item = self.get_object()
        item.name= request.data.get('name', item.name)
        item.save()
        res = ItemSerializer(item)
        return Response({"message": "updated successfully", "data": res.data}, status=status.HTTP_200_OK)

def index(request):
    return HttpResponse("Welcome to REVENUE COMPLIANCE MANAGEMENT Server API Page")