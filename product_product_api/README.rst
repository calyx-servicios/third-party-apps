============
Product Api
============

.. !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
   !! This file is intended to be in every module    !!
   !! to explain why and how it works.               !!
   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


.. User https://shields.io for badge creation.
.. |badge1| image:: https://img.shields.io/badge/maturity-Stable-brightgreen
    :target: https://odoo-community.org/page/development-status
    :alt: Stable
.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3
.. |badge3| image:: https://img.shields.io/badge/gitlab-calyxservicios--group%2Fodoo%2Fodoo--calyx-lightgray.png?logo=gitlab
    :target: https://gitlab.com/calyxservicios-group/odoo/odoo-calyx
    :alt: calyxservicios-group/odoo/odoo-calyx

|badge1| |badge2| |badge3|

.. !!! Description must be max 2-3 paragraphs, and is required.

This module create a controller and allows to you get information in json format from product.product. 

**Table of contents**

.. contents::
   :local:

.. !!! Instalation: must only be present if there are very specific installation instructions, such as installing non-python dependencies.The audience is systems administrators. ] To install this module, you need to: !!!

Install
=======

Install the Module


Usage
=====

1. Loggin by /web/session/authenticate url using "content_type='application/json'" header and this params:
    
    {
        "jsonrpc": "2.0",
        "params":{
            "db":"DBNAME",
            "login": "USER",
            "password": "PASSWORD"
        }
    }
 
2.
    2.1.- Using the url /get_products with the header and the params:
        {
            "jsonrpc": "2.0",
            "params":{
                "categ": #Name of category of products,
                "product": #Name of the product,
                "values": #Name of attribute values,
                "pos_categ": #Name of pos category,
            }
        } 

    2.2.- Get the information.


Known issues / Roadmap
======================

* Bugs or Roadmap

Bug Tracker
===========

* Help Contact

Credits
=======

Authors
~~~~~~~

* Calyx Servicios S.A.

Contributors
~~~~~~~~~~~~

* `Calyx Servicios S.A. <http://odoo.calyx-cloud.com.ar/>`_
  
  * Jhone Mendez
  * Federico Gregori
  * Milton Guzman
  * Christian Paradiso

Maintainers
~~~~~~~~~~~

This module is maintained by the Calyx Servicios S.A.

.. image:: https://ss-static-01.esmsv.com/id/13290/galeriaimagenes/obtenerimagen/?width=120&height=40&id=sitio_logo&ultimaModificacion=2020-05-25+21%3A45%3A05
   :alt: Odoo Calyx Servicios S.A.
   :target: http://odoo.calyx-cloud.com.ar/

CALYX SERVICIOS S.A. It is part of the PGK Consultores economic group, member of an important global network, a world organization positioned among the 20 largest consultant-studios in the world.
The PGK Consultores group is one of the 20 largest consultant-studios in Argentina with nearly 200 professionals.

This module is part of the `Calyx-web <https://github.com/calyx-servicios/web>`_ project on GitHub.