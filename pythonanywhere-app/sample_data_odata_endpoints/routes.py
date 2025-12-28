# Sample Data OData Endpoints Blueprint
# This project provides OData v4 endpoints with sample data for testing/demonstration

import json
from flask import Blueprint, request, Response

# Create blueprint
sample_data_bp = Blueprint('sample_data', __name__, url_prefix='/sample_data')

@sample_data_bp.route("/$metadata")
def metadata():
    """OData v4 metadata document describing the SampleData entity"""
    metadata_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<edmx:Edmx xmlns:edmx="http://docs.oasis-open.org/odata/ns/edmx" Version="4.0">
  <edmx:DataServices>
    <Schema xmlns="http://docs.oasis-open.org/odata/ns/edm" Namespace="SampleDataService">
      <EntityType Name="SampleDataItem">
        <Key>
          <PropertyRef Name="Date"/>
        </Key>
        <Property Name="Date" Type="Edm.String" Nullable="false"/>
        <Property Name="Value" Type="Edm.Int32" Nullable="false"/>
      </EntityType>
      <EntityContainer Name="Container">
        <EntitySet Name="SampleData" EntityType="SampleDataService.SampleDataItem"/>
      </EntityContainer>
    </Schema>
  </edmx:DataServices>
</edmx:Edmx>'''
    return Response(metadata_xml, mimetype='application/xml', headers={'OData-Version': '4.0'})

@sample_data_bp.route("/")
def service_doc():
    """OData v4 service document"""
    service_doc = {
        "@odata.context": f"{request.url_root}sample_data/$metadata",
        "value": [
            {
                "name": "SampleData",
                "kind": "EntitySet",
                "url": "SampleData"
            }
        ]
    }
    return Response(
        json.dumps(service_doc),
        mimetype='application/json',
        headers={
            'OData-Version': '4.0',
            'Content-Type': 'application/json; odata.metadata=minimal'
        }
    )

@sample_data_bp.route("/SampleData")
def sample_data():
    """OData v4 Data endpoint with sample data"""
    # Sample data using ISO date format for Tableau compatibility
    data = [
        {"Date": "2025-12-15", "Value": 41},
        {"Date": "2025-12-16", "Value": 52},
        {"Date": "2025-12-17", "Value": 27},
        {"Date": "2025-12-18", "Value": 33},
        {"Date": "2025-12-19", "Value": 42},
        {"Date": "2025-12-20", "Value": 41}
    ]

    # Apply OData query parameters
    args = request.args

    # $filter - basic support for simple equality filters
    if '$filter' in args:
        filter_expr = args['$filter']
        # Simple parsing for "Date eq 'value'" or "Value eq number"
        if ' eq ' in filter_expr:
            field, value = filter_expr.split(' eq ')
            field = field.strip()
            value = value.strip().strip("'")
            if field == 'Value':
                value = int(value)
            data = [item for item in data if str(item.get(field)) == str(value)]

    # $select - select specific fields
    if '$select' in args:
        fields = [f.strip() for f in args['$select'].split(',')]
        data = [{k: v for k, v in item.items() if k in fields} for item in data]

    # $orderby - sort data
    if '$orderby' in args:
        orderby = args['$orderby']
        reverse = False
        if ' desc' in orderby:
            orderby = orderby.replace(' desc', '').strip()
            reverse = True
        elif ' asc' in orderby:
            orderby = orderby.replace(' asc', '').strip()
        data = sorted(data, key=lambda x: x.get(orderby, ''), reverse=reverse)

    # $top - limit number of results
    if '$top' in args:
        top = int(args['$top'])
        data = data[:top]

    # $skip - skip number of results
    if '$skip' in args:
        skip = int(args['$skip'])
        data = data[skip:]

    # $count - return count
    if '$count' in args and args['$count'].lower() == 'true':
        odata_response = {
            "@odata.context": f"{request.url_root}sample_data/$metadata#SampleData",
            "@odata.count": len(data),
            "value": data
        }
    else:
        # OData response format
        odata_response = {
            "@odata.context": f"{request.url_root}sample_data/$metadata#SampleData",
            "value": data
        }

    return Response(
        json.dumps(odata_response),
        mimetype='application/json',
        headers={
            'OData-Version': '4.0',
            'Content-Type': 'application/json; odata.metadata=minimal'
        }
    )
