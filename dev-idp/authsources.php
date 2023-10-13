<?php
# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

# Her opsættes demobrugere og deres data

$test_user_base = array(
    'http://schemas.microsoft.com/identity/claims/tenantid' => 'ab4f07dc-b661-48a3-a173-d0103d6981b2',
    'http://schemas.microsoft.com/identity/claims/objectidentifier' => '',
    'http://schemas.microsoft.com/identity/claims/displayname' => '',
    'http://schemas.microsoft.com/ws/2008/06/identity/claims/groups' => array(),
    'http://schemas.microsoft.com/identity/claims/identityprovider' => 'https://sts.windows.net/da2a1472-abd3-47c9-95a4-4a0068312122/',
    'http://schemas.microsoft.com/claims/authnmethodsreferences' => array('http://schemas.microsoft.com/ws/2008/06/identity/authenticationmethod/password', 'http://schemas.microsoft.com/claims/multipleauthn'),
    'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress' => '',
    'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname' => '',
    'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname' => '',
    'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name' => ''
);

$config = array(
    'admin' => array(
        'core:AdminPassword',''
    ),
    'example-userpass' => array(
        'exampleauth:UserPass',
        
        'indberetter:indberetter' => array_merge($test_user_base, array(
            'http://schemas.microsoft.com/identity/claims/objectidentifier' => 'f2d75402-e1ae-40fe-8cc9-98ca1ab9cd5f',
            'http://schemas.microsoft.com/identity/claims/displayname' => 'Indberetter',
            'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress' => 'indberetter@example.com',
            'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname' => 'Indberetter',
            'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname' => '1',
            'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name' => 'indberetter@example.com',

            # Claims fra OIOSAML
            'https://data.gov.dk/model/core/specVersion' => 'OIO-SAML-3.0',
            'https://data.gov.dk/concept/core/nsis/loa' => 'Substantial',
            'https://data.gov.dk/concept/core/nsis/ial' => 'Substantial',
            'https://data.gov.dk/concept/core/nsis/aal' => 'High',
            'https://data.gov.dk/model/core/eid/fullName' => 'Anders And',
            'https://data.gov.dk/model/core/eid/firstName' => 'Anders',
            'https://data.gov.dk/model/core/eid/lastName' => 'And',
            'https://data.gov.dk/model/core/eid/email' => 'anders@andeby.dk',
            'https://data.gov.dk/model/core/eid/cprNumber' => '1111111111',
            'https://data.gov.dk/model/core/eid/age' => '60',
            'https://data.gov.dk/model/core/eid/cprUuid' => 'urn:uuid:323e4567-e89b-12d3-a456-
426655440000',
            'https://data.gov.dk/model/core/eid/professional/cvr' => '12345678',
            'https://data.gov.dk/model/core/eid/professional/orgName' => 'Joakim von Ands pengetank',
            'https://data.gov.dk/model/core/eid/professional/productionUnit' => '8888888888',
            'https://data.gov.dk/model/core/eid/professional/seNumber' => '77777777',
            'https://data.gov.dk/model/core/eid/professional/authorizedToRepresent' => '66666666',
            'https://data.gov.dk/model/core/eid/privilegesIntermediate' =>
                'PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4KPGJwcDpQcml2aWxlZ2VMaXN0
                CnhtbG5zOmJwcD0iaHR0cDovL2l0c3QuZGsvb2lvc2FtbC9iYXNpY19wcml2aWxlZ2VfcHJvZmls
                ZSIKeG1sbnM6eHNpPSJodHRwOi8vd3d3LnczLm9yZy8yMDAxL1hNTFNjaGVtYS1pbnN0YW5jZSIg
                Pgo8UHJpdmlsZWdlR3JvdXAgU2NvcGU9InVybjpkazpnb3Y6c2FtbDpjdnJOdW1iZXJJZGVudGlm
                aWVyOjEyMzQ1Njc4Ij4KPFByaXZpbGVnZT51cm46ZGs6c29tZV9kb21haW46bXlQcml2aWxlZ2Ux
                QTwvUHJpdmlsZWdlPgo8UHJpdmlsZWdlPnVybjpkazpzb21lX2RvbWFpbjpteVByaXZpbGVnZTFC
                PC9Qcml2aWxlZ2U+CjwvUHJpdmlsZWdlR3JvdXA+CjxQcml2aWxlZ2VHcm91cCBTY29wZT0idXJu
                OmRrOmdvdjpzYW1sOnNlTnVtYmVySWRlbnRpZmllcjoyNzM4NDIyMyI+CjxQcml2aWxlZ2U+dXJu
                OmRrOnNvbWVfZG9tYWluOm15UHJpdmlsZWdlMUM8L1ByaXZpbGVnZT4KPFByaXZpbGVnZT51cm46
                ZGs6c29tZV9kb21haW46bXlQcml2aWxlZ2UxRDwvUHJpdmlsZWdlPgo8L1ByaXZpbGVnZUdyb3Vw
                Pgo8L2JwcDpQcml2aWxlZ2VMaXN0Pgo='
        )),

        'indberetter2:indberetter2' => array_merge($test_user_base, array(
            'http://schemas.microsoft.com/identity/claims/objectidentifier' => 'f2d75402-e1ae-40fe-8cc9-98ca1ab9cd5e',
            'http://schemas.microsoft.com/identity/claims/displayname' => 'Indberetter2',
            'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress' => 'indberetter2@example.com',
            'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname' => 'Indberetter',
            'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname' => '2',
            'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name' => 'indberetter2@example.com',

            # Claims fra OIOSAML
            'https://data.gov.dk/model/core/specVersion' => 'OIO-SAML-3.0',
            'https://data.gov.dk/concept/core/nsis/loa' => 'Substantial',
            'https://data.gov.dk/concept/core/nsis/ial' => 'Substantial',
            'https://data.gov.dk/concept/core/nsis/aal' => 'High',
            'https://data.gov.dk/model/core/eid/fullName' => 'Mickey Mouse',
            'https://data.gov.dk/model/core/eid/firstName' => 'Mickey',
            'https://data.gov.dk/model/core/eid/lastName' => 'Mouse',
            'https://data.gov.dk/model/core/eid/email' => 'mickey@andeby.dk',
            'https://data.gov.dk/model/core/eid/cprNumber' => '1111111112',
            'https://data.gov.dk/model/core/eid/age' => '60',
            'https://data.gov.dk/model/core/eid/cprUuid' => 'urn:uuid:323e4567-e89b-12d3-a456-
426655440000',
            'https://data.gov.dk/model/core/eid/professional/cvr' => '12345678',
            'https://data.gov.dk/model/core/eid/professional/orgName' => 'Joakim von Ands pengetank',
            'https://data.gov.dk/model/core/eid/professional/productionUnit' => '8888888888',
            'https://data.gov.dk/model/core/eid/professional/seNumber' => '77777777',
            'https://data.gov.dk/model/core/eid/professional/authorizedToRepresent' => '66666666',
            'https://data.gov.dk/model/core/eid/privilegesIntermediate' =>
                'PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4KPGJwcDpQcml2aWxlZ2VMaXN0
                CnhtbG5zOmJwcD0iaHR0cDovL2l0c3QuZGsvb2lvc2FtbC9iYXNpY19wcml2aWxlZ2VfcHJvZmls
                ZSIKeG1sbnM6eHNpPSJodHRwOi8vd3d3LnczLm9yZy8yMDAxL1hNTFNjaGVtYS1pbnN0YW5jZSIg
                Pgo8UHJpdmlsZWdlR3JvdXAgU2NvcGU9InVybjpkazpnb3Y6c2FtbDpjdnJOdW1iZXJJZGVudGlm
                aWVyOjEyMzQ1Njc4Ij4KPFByaXZpbGVnZT51cm46ZGs6c29tZV9kb21haW46bXlQcml2aWxlZ2Ux
                QTwvUHJpdmlsZWdlPgo8UHJpdmlsZWdlPnVybjpkazpzb21lX2RvbWFpbjpteVByaXZpbGVnZTFC
                PC9Qcml2aWxlZ2U+CjwvUHJpdmlsZWdlR3JvdXA+CjxQcml2aWxlZ2VHcm91cCBTY29wZT0idXJu
                OmRrOmdvdjpzYW1sOnNlTnVtYmVySWRlbnRpZmllcjoyNzM4NDIyMyI+CjxQcml2aWxlZ2U+dXJu
                OmRrOnNvbWVfZG9tYWluOm15UHJpdmlsZWdlMUM8L1ByaXZpbGVnZT4KPFByaXZpbGVnZT51cm46
                ZGs6c29tZV9kb21haW46bXlQcml2aWxlZ2UxRDwvUHJpdmlsZWdlPgo8L1ByaXZpbGVnZUdyb3Vw
                Pgo8L2JwcDpQcml2aWxlZ2VMaXN0Pgo='
        )),


        'user2:foobar' => array_merge($test_user_base, array(
            'http://schemas.microsoft.com/identity/claims/objectidentifier' => 'f2d75402-e1ae-40fe-8cc9-98ca1ab9cd5e',
            'http://schemas.microsoft.com/identity/claims/displayname' => 'User1 Taro',
            'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress' => 'user1@example.com',
            'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname' => 'Taro',
            'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname' => 'User1',
            'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name' => 'user1@example.com',

            # Claims fra OIOSAML
            'https://data.gov.dk/model/core/specVersion' => 'OIO-SAML-3.0',
            'https://data.gov.dk/concept/core/nsis/loa' => 'Substantial',
            'https://data.gov.dk/concept/core/nsis/ial' => 'Substantial',
            'https://data.gov.dk/concept/core/nsis/aal' => 'High',
            'https://data.gov.dk/model/core/eid/fullName' => 'Andersine And',
            'https://data.gov.dk/model/core/eid/firstName' => 'Anders',
            'https://data.gov.dk/model/core/eid/lastName' => 'And',
            'https://data.gov.dk/model/core/eid/email' => 'anders@andeby.dk',
            'https://data.gov.dk/model/core/eid/cprNumber' => '1234567890',
            'https://data.gov.dk/model/core/eid/age' => '60',
            'https://data.gov.dk/model/core/eid/cprUuid' => 'urn:uuid:323e4567-e89b-12d3-a456-
426655440000',
            'https://data.gov.dk/model/core/eid/professional/cvr' => '12345678',
            'https://data.gov.dk/model/core/eid/professional/orgName' => 'Ikke relevant',
            'https://data.gov.dk/model/core/eid/professional/productionUnit' => '8888888888',
            'https://data.gov.dk/model/core/eid/professional/seNumber' => '77777777',
            'https://data.gov.dk/model/core/eid/professional/authorizedToRepresent' => '66666666',
            'https://data.gov.dk/model/core/eid/privilegesIntermediate' =>
                'PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4KPGJwcDpQcml2aWxlZ2VMaXN0
                CnhtbG5zOmJwcD0iaHR0cDovL2l0c3QuZGsvb2lvc2FtbC9iYXNpY19wcml2aWxlZ2VfcHJvZmls
                ZSIKeG1sbnM6eHNpPSJodHRwOi8vd3d3LnczLm9yZy8yMDAxL1hNTFNjaGVtYS1pbnN0YW5jZSIg
                Pgo8UHJpdmlsZWdlR3JvdXAgU2NvcGU9InVybjpkazpnb3Y6c2FtbDpjdnJOdW1iZXJJZGVudGlm
                aWVyOjEyMzQ1Njc4Ij4KPFByaXZpbGVnZT51cm46ZGs6c29tZV9kb21haW46bXlQcml2aWxlZ2Ux
                QTwvUHJpdmlsZWdlPgo8UHJpdmlsZWdlPnVybjpkazpzb21lX2RvbWFpbjpteVByaXZpbGVnZTFC
                PC9Qcml2aWxlZ2U+CjwvUHJpdmlsZWdlR3JvdXA+CjxQcml2aWxlZ2VHcm91cCBTY29wZT0idXJu
                OmRrOmdvdjpzYW1sOnNlTnVtYmVySWRlbnRpZmllcjoyNzM4NDIyMyI+CjxQcml2aWxlZ2U+dXJu
                OmRrOnNvbWVfZG9tYWluOm15UHJpdmlsZWdlMUM8L1ByaXZpbGVnZT4KPFByaXZpbGVnZT51cm46
                ZGs6c29tZV9kb21haW46bXlQcml2aWxlZ2UxRDwvUHJpdmlsZWdlPgo8L1ByaXZpbGVnZUdyb3Vw
                Pgo8L2JwcDpQcml2aWxlZ2VMaXN0Pgo='
        )),
    )
);
