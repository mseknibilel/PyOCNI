# -*- Mode: python; py-indent-offset: 4; indent-tabs-mode: nil; coding: utf-8; -*-

# Copyright (C) 2011 Houssem Medhioub - Institut Mines-Telecom
#
# This library is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.

"""
Created on Jun 12, 2012

@author: Bilel Msekni
@contact: bilel.msekni@telecom-sudparis.eu
@author: Houssem Medhioub
@contact: houssem.medhioub@it-sudparis.eu
@organization: Institut Mines-Telecom - Telecom SudParis
@version: 0.3
@license: LGPL - Lesser General Public License
"""

import pyocni.pyocni_tools.config as config
import pyocni.pyocni_tools.occi_Joker as joker
try:
    import simplejson as json
except ImportError:
    import json
from datetime import datetime
from pyocni.pyocni_tools import uuid_Generator
from pyocni.pyocni_tools.config import return_code

# getting the Logger
logger = config.logger

#=======================================================================================================================
#                                           ResourceManager
#=======================================================================================================================

class ResourceManager(object):
    """
    Manager of resource and link documents in the couch database.
    """

    def register_resources(self,creator,occi_descriptions,url_path,db_occi_ids_locs):

        """
        Add new resources to the database
        Args:
            @param creator: the user who created these new resources
            @param occi_descriptions: the OCCI description of the new resources
            @param db_occi_ids_locs: OCCI IDs and OCCI Location extracted from the database
            @param url_path: URL path of the request
        """
        loc_res = list()
        kind_occi_id = None
        for elem in db_occi_ids_locs:
            if elem['OCCI_Location'] == url_path:
                kind_occi_id = elem['OCCI_ID']
                break
        if kind_occi_id is not None:
            for desc in occi_descriptions:

                #Verify if the kind to which this request is sent is the same as the one in the link description
                if desc['kind'] == kind_occi_id:
                    if desc.has_key('actions'):
                        ok_a = joker.verify_existences_delta(desc['actions'],db_occi_ids_locs)
                    else:
                        ok_a = True
                    if ok_a is True:
                        if desc.has_key('mixins'):
                            ok_m = joker.verify_existences_beta(desc['mixins'],db_occi_ids_locs)
                        else:
                            ok_m = True
                        if ok_m is True:
                            if desc.has_key('links'):
                                ok_l,exist_links = self.verify_links_implicit(desc['links'],creator,db_occi_ids_locs)
                            else:
                                ok_l = True
                                exist_links = False
                            if ok_l is True:
                                loc = joker.make_entity_location_from_url(creator,url_path,desc['id'])
                                exist_same = joker.verify_existences_teta([loc],db_occi_ids_locs)
                                if exist_same is False:
                                    jData = dict()
                                    jData['_id'] = uuid_Generator.get_UUID()
                                    jData['Creator'] = creator
                                    jData['CreationDate'] = str(datetime.now())
                                    jData['LastUpdate'] = ""
                                    jData['OCCI_Location']= loc
                                    jData['OCCI_Description']= desc
                                    jData['Type']= "Resource"
                                    jData['Internal_Links'] = exist_links
                                    loc_res.append(jData)
                                else:
                                    logger.error("Reg resource exp : Bad Resource id ")
                                    return list(),return_code['Conflict']
                            else:
                                logger.error("Reg resources exp : Bad links description ")
                                return list(),exist_links
                        else:
                            logger.error("Reg resources exp : Bad Mixins description ")
                            return list(),return_code['Not Found']
                    else:
                        logger.error("Reg resources exp : Bad Actions description ")
                        return list(),return_code['Not Found']
                else:
                    mesg = "Kind description and kind location don't match"
                    logger.error("Reg resources exp: " + mesg)
                    return list(),return_code['Conflict']
            logger.debug("Reg resouces exp: Resources sent for creation")
            return loc_res,return_code['OK']
        else:
            mesg = "No kind corresponding to this location was found"
            logger.error("Reg resources exp: " + mesg)
            return list(),return_code['Not Found']


    def verify_links_implicit(self,occi_descriptions,creator,db_occi_ids_locs):
        """
        Checks the integrity of internal resource links (Called only during the creation of a new resource instance)
        Args:

            @param occi_descriptions: the OCCI descriptions of new links
            @param creator: Issuer of the request
            @param db_occi_ids_locs: OCCI IDs and locations contained in the database
        """
        impl_link_locs = list()
        for desc in occi_descriptions:
            ok_k = joker.verify_existences_beta([desc['kind']],db_occi_ids_locs)
            #Verify if the kind to which this request is sent is the same as the one in the link description
            if ok_k is True:
                ok_target = joker.verify_existences_teta([desc['target']],db_occi_ids_locs)
                if ok_target is True:
                    if desc.has_key('actions'):
                        ok_a = joker.verify_existences_delta(desc['actions'],db_occi_ids_locs)
                    else:
                        ok_a = True
                    if ok_a is True:
                        if desc.has_key('mixins'):
                            ok_m = joker.verify_existences_beta(desc['mixins'],db_occi_ids_locs)
                        else:
                            ok_m = True
                        if ok_m is True:
                            loc = joker.make_implicit_link_location(desc['id'],desc['kind'],creator,db_occi_ids_locs)
                            exist_same = joker.verify_existences_teta([loc],db_occi_ids_locs)
                            if exist_same is True:
                                logger.error("Reg links impl : Bad link id ")
                                return False,return_code['Conflict']
                            else:
                                impl_link_locs.append(loc)
                        else:
                            logger.error("Reg links impl : Bad Mixins description ")
                            return False,return_code['Not Found']
                    else:
                        logger.error("Reg links impl : Bad Actions description ")
                        return False,return_code['Not Found']
                else:
                    logger.error("Reg links impl : Bad target description ")
                    return False,return_code['Not Found']
            else:
                mesg = "Kind description does not exist"
                logger.error("Reg links impl: " + mesg)
                return False,return_code['Not Found']
        logger.debug("Internal links validated with success")
        return True,impl_link_locs

    def get_filtered_resources(self, filters, descriptions_res):
        """
        Retrieve the resources  that match the filters provided
        Args:
            @param filters: Filters
            @param descriptions_res: Resource descriptions
        """
        var = list()
        try:
            for desc in descriptions_res:
                for filter in filters:
                    checks =joker.filter_occi_description(desc['OCCI_Description'],filter)
                    if checks is True:
                        var.append(desc['OCCI_ID'])
                        logger.debug("Entity filtered : document found")
                        break
            return var,return_code['OK']
        except Exception as e:
            logger.error("filtered res : " + e.message)
            return "An error has occurred",return_code['Internal Server Error']

#=======================================================================================================================
#                                           LinkManager
#=======================================================================================================================

class LinkManager(object):
    """
    Manager of link documents in the couch database.
    """

    def register_links_explicit(self,creator,occi_descriptions,url_path,db_occi_ids_locs):
        """
        Add new links to database
        Args:
            @param creator: Issuer of the register request
            @param occi_descriptions: Link OCCI descriptions
            @param db_occi_ids_locs: OCCI ID and locations extracted from the database
            @param url_path: URL path of the request
        """

        loc_res = list()
        kind_occi_id = None
        for elem in db_occi_ids_locs:
            if elem['OCCI_Location'] == url_path:
                kind_occi_id = elem['OCCI_ID']
                break
        if kind_occi_id is not None:
            for desc in occi_descriptions:

                #Verify if the kind to which this request is sent is the same as the one in the link description
                if desc['kind'] == kind_occi_id:

                    ok_target_source = joker.verify_existences_teta([desc['target'],desc['source']],db_occi_ids_locs)
                    if ok_target_source is True:
                        ok_kappa = joker.verify_existences_kappa([desc['target'],desc['source']],db_occi_ids_locs)
                        if ok_kappa is True:
                            if desc.has_key('actions'):
                                ok_a = joker.verify_existences_delta(desc['actions'],db_occi_ids_locs)
                            else:
                                ok_a = True
                            if ok_a is True:
                                if desc.has_key('mixins'):
                                    ok_m = joker.verify_existences_beta(desc['mixins'],db_occi_ids_locs)
                                else:
                                    ok_m = True
                                if ok_m is True:
                                    loc = joker.make_entity_location_from_url(creator,url_path,desc['id'])
                                    exist_same = joker.verify_existences_teta([loc],db_occi_ids_locs)
                                    if exist_same is False:
                                        jData = dict()
                                        jData['_id'] = uuid_Generator.get_UUID()
                                        jData['Creator'] = creator
                                        jData['CreationDate'] = str(datetime.now())
                                        jData['LastUpdate'] = ""
                                        jData['OCCI_Location']= loc
                                        jData['OCCI_Description']= desc
                                        jData['Type']= "Link"
                                        loc_res.append(jData)
                                    else:
                                        logger.error("Reg links exp : Bad Link id ")
                                        return list(),return_code['Conflict']
                                else:
                                    logger.error("Reg links exp : Bad Mixins description ")
                                    return list(),return_code['Not Found']
                            else:
                                logger.error("Reg links exp : Bad Actions description ")
                                return list(),return_code['Not Found']
                        else:
                            logger.error("Reg links exp : Bad resources description ")
                            return list(),return_code['Bad Request']
                    else:
                        logger.error("Reg links exp : Bad resources description ")
                        return list(),return_code['Not Found']
                else:
                    mesg = "Kind description and kind location don't match"
                    logger.error("Reg links exp: " + mesg)
                    return list(),return_code['Conflict']
            logger.debug("Reg links exp: links sent for creation")
            return loc_res,return_code['OK']
        else:
            mesg = "No kind corresponding to this location was found"
            logger.error("Reg links exp: " + mesg)
            return list(),return_code['Not Found']


    def get_filtered_links(self, filters, descriptions_link):
        """
        Retrieve the resources  that match the filters provided
        Args:
            @param filters: Filters
            @param descriptions_link: Link descriptions
        """
        var = list()
        try:
            for desc in descriptions_link:
                for filter in filters:
                    checks =joker.filter_occi_description(desc['OCCI_Description'],filter)
                    if checks is True:
                        var.append(desc['OCCI_ID'])
                        logger.debug("Entity filtered : document found")
                        break
            return var,return_code['OK']
        except Exception as e:
            logger.error("filtered link : " + e.message)
            return "An error has occurred",return_code['Internal Server Error']

#=======================================================================================================================
#                                           MultiEntityManager
#=======================================================================================================================

class MultiEntityManager(object):
    """

    """

    def __init__(self):

        self.manager_r = ResourceManager()
        self.manager_l = LinkManager()

    def channel_post_multi(self,user_id,jreq,req_path):
        """
        Identifies the post path's goal : create a resource instance or update a mixin
        Args:
            @param user_id: ID of the issuer of the post request
            @param jreq: Body content of the post request
            @param req_path: Address to which this post request was sent
        """
        url_path = joker.reformat_url_path(req_path)
        database = config.prepare_PyOCNI_db()

        if jreq.has_key('resources') or jreq.has_key('links'):
            is_kind_loc = True
        else:
            is_kind_loc = False

        if is_kind_loc is True:
            try:
                query = database.view('/db_views/for_register_entities')
            except Exception as e:
                logger.error("post multi entities : " + e.message)
                return "An error has occurred, please check log for more details",return_code['Internal Server Error']
            db_occi_ids_locs = list()
            for q in query:
                db_occi_ids_locs.append({"OCCI_ID" : q['key'],"OCCI_Location":q['value']})

            if jreq.has_key('resources'):
                logger.debug("Post path : Post on kind path to create a new resource channeled")
                new_resources, resp_code_r = self.manager_r.register_resources(user_id,jreq['resources'],url_path,db_occi_ids_locs)
            else:
                new_resources = list()
                resp_code_r = return_code['OK']

            if jreq.has_key('links'):
                logger.debug("Post path : Post on kind path to create a new link channeled")
                new_links, resp_code_l = self.manager_l.register_links_explicit(user_id,jreq['links'],url_path,db_occi_ids_locs)
            else:
                new_links = list()
                resp_code_l = return_code['OK']

            if resp_code_r is not return_code['OK'] or resp_code_l is not return_code['OK']:
                return "An error has occurred, please check log for more details",return_code['Bad Request']

            entities = new_resources + new_links
            database.save_docs(entities,use_uuids=True, all_or_nothing=True)
            #return the locations of the resources
            return "",return_code['OK']

        else:
            if jreq.has_key('OCCI_Locations'):
                db_docs = list()
                try:
                    query = database.view('/db_views/my_mixins',key = url_path)
                except Exception as e:
                    logger.error("Associate mixins : " + e.message)
                    return "An error has occurred, please check log for more details",return_code['Internal Server Error']
                if query.count() is 0:
                    logger.error("Associate a mixin  : " + url_path)
                    return "An error has occurred, please check log for more details",return_code['Not Found']
                else:
                    mix_id = query.first()['value']
                    to_search_for = jreq['OCCI_Locations']
                    for item in to_search_for:
                        try:
                            query = database.view('/db_views/for_associate_mixin',key=[item,user_id])
                        except Exception as e:
                            logger.error("Associate a mixin : " + e.message)
                            return "An error has occurred, please check log for more details",return_code['Internal Server Error']

                        if query.count() is 0:
                            logger.error("Associate a mixin  : " + item)
                            return "An error has occurred, please check log for more details",return_code['Not Found']
                        else:
                            q = query.first()
                            db_docs.append(q['value'])

                        logger.debug("Post path : Post on mixin path to associate a mixin channeled")
                        updated_entities,resp_code_e = associate_entities_to_a_mixin(mix_id,db_docs)
            else:
                updated_entities = list()
                resp_code_e = return_code['OK']

            if resp_code_e is not return_code['OK']:
                return "An error has occurred, please check log for more details",return_code['Bad Request']

            database.save_docs(updated_entities,force_update=True,all_or_nothing=True)
            return "",return_code['OK']

    def channel_get_all_entities(self,req_path):
        """
        retrieve all entities belonging to a kind or a mixin
        Args:
            @param req_path: Address to which this post request was sent
        """
        url_path = joker.reformat_url_path(req_path)
        database = config.prepare_PyOCNI_db()
        try:
            query = database.view('/db_views/for_get_entities',key=url_path)
        except Exception as e:
            logger.error("get all multi entities : " + e.message)
            return "An error has occurred, please check log for more details",return_code['Internal Server Error']
        if query.count() is 0:
            logger.error("get all multi entities  : " + url_path)
            return "An error has occurred, please check log for more details",return_code['Not Found']
        else:
            q = query.first()
            if q['value'][1] == "Kind":
                try:
                    kind_id = q['value'][0]
                    entities = database.view('/db_views/entities_of_kind',key = kind_id)
                except Exception as e:
                    logger.error("get all multi entities : " + e.message)
                    return "An error has occurred, please check log for more details",return_code['Internal Server Error']
            elif q['value'][1] == "Mixin":
                try:
                    mix_id = q['value'][0]
                    entities = database.view('/db_views/entities_of_mixin',key = mix_id)
                except Exception as e:
                    logger.error("get all multi entities : " + e.message)
                    return "An error has occurred, please check log for more details",return_code['Internal Server Error']
            else:
                logger.error("get all multi entities : Unknown " + q['value'][1])
                return "An error has occurred, please check log for more details",return_code['Internal Server Error']
        to_return_res = list()
        to_return_link = list()
        for entity in entities:
            if entity['value'][1] == "Resource":
                to_return_res.append(entity['value'][0])
            else:
                to_return_link.append((entity['value'][0]))
        result = to_return_res + to_return_link
        return result,return_code['OK']

    def channel_get_filtered_entities(self,req_path,terms):
        """
        Retrieve entities belonging to a kind or a mixin matching the terms specified
        Args:
            @param req_path: Address to which this post request was sent
            @param terms: Terms to filter entities
        """
        descriptions_res = list()
        descriptions_link = list()
        database = config.prepare_PyOCNI_db()
        try:
            entities,ok = self.channel_get_all_entities(req_path)
            entities = entities['links'] + entities['resources']
            if ok == return_code['OK']:
                for entity in entities:
                    try:
                        query = database.view('/db_views/for_get_filtered',key=entity)
                        if query.first()['value'][1] == "Resource":
                            descriptions_res.append({'OCCI_ID' : entity,'OCCI_Description' : query.first()['value'][0]})
                        else:
                            descriptions_link.append({'OCCI_ID' : entity,'OCCI_Description' : query.first()['value'][0]})
                    except Exception as e:
                        logger.error("get filtered entities : " + e.message)
                        return "An error has occurred, please check log for more details",return_code['Internal Server Error']
                if terms.has_key('resources'):
                    logger.debug("Resources filter get request : channeled")
                    filtered_res,resp_code_r = self.manager_r.get_filtered_resources(terms['resources'],descriptions_res)
                else:
                    logger.debug("Resources get filter : res not found")
                    filtered_res = ""
                    resp_code_r = return_code['OK']
                if terms.has_key('links'):
                    logger.debug("links filter get request : channeled")
                    filtered_links,resp_code_l = self.manager_l.get_filtered_links(terms['links'],descriptions_link)
                else:
                    logger.debug("Links get filter : link not found")
                    filtered_links = ""
                    resp_code_l = return_code['OK']

                if resp_code_l is not 200 or resp_code_r is not 200:
                    return "An error has occurred, please check log for more details",return_code['Bad Request']

                result = filtered_res + filtered_links
                return result,return_code['OK']
            else:
                return entities,ok

        except Exception as e:
            logger.error("filtered entities : " + e.message)
            return "An error has occurred, please check log for more details",return_code['Internal Server Error']

    def channel_put_multi(self, user_id, jreq, req_url):
        """
        Update the mixin collection of resources
        Args:
            @param user_id: The issuer of the request
            @param jreq: OCCI_Locations of the resources
            @param req_url: URL of the request
        """
        database = config.prepare_PyOCNI_db()
        if jreq.has_key('Resource_Locations') and jreq.has_key('Mixin_Locations'):
            url_path = joker.reformat_url_path(req_url)
            db_docs = list()
            to_validate = jreq['Mixin_Locations']
            to_validate.append(url_path)
            mix_ids = list()
            for occi_loc in to_validate:
                try:
                    query = database.view('/db_views/my_mixins',key = occi_loc)
                except Exception as e:
                    logger.error("Associate mixins : " + e.message)
                    return "An error has occurred, please check log for more details",return_code['Internal Server Error']
                if query.count() is 0:
                    logger.error("Associate mixins : " + occi_loc)
                    return "An error has occurred, please check log for more details",return_code['Internal Server Error']
                else:
                    mix_ids.append(query.first()['value'])

            to_search_for = jreq['Resource_Locations']
            for item in to_search_for:
                try:
                    query = database.view('/db_views/for_associate_mixin',key=[item,user_id])
                except Exception as e:
                    logger.error("Associate mixins : " + e.message)
                    return "An error has occurred, please check log for more details",return_code['Internal Server Error']
                if query.count() is 0:
                    logger.error("Associate mixins  : " + item)
                    return "An error has occurred, please check log for more details",return_code['Not Found']
                else:
                    q = query.first()
                    db_docs.append(q['value'])

            logger.debug("Post path : Post on mixin path to associate mixins channeled")
            updated_entities,resp_code_e = associate_entities_to_mixins(mix_ids,db_docs)
        else:
            updated_entities = list()
            resp_code_e = return_code['Bad Request']

        if resp_code_e is not return_code['OK']:
            return "An error has occurred, please check log for more details",return_code['Bad Request']

        database.save_docs(updated_entities,force_update=True,all_or_nothing=True)
        return "",return_code['OK']

#=======================================================================================================================
#                                           SingleEntityManager
#=======================================================================================================================

class SingleEntityManager(object):
    """

    """

    def __init__(self):

        self.manager_r = ResourceManager()
        self.manager_l = LinkManager()

#=======================================================================================================================
#                                           Independent Functions
#=======================================================================================================================

def associate_entities_to_a_mixin( mix_id, db_docs):
    """
    Add a single mixin to entities
    Args:
        @param mix_id: OCCI ID of the mixin
        @param db_docs: documents of the entities already contained in the database
    """
    if mix_id is not None:
        for doc in db_docs:
            if doc['OCCI_Description'].has_key('mixins'):
                var = doc['OCCI_Description']['mixins']
                try:
                    var.index(mix_id)
                except ValueError:
                    var.append(mix_id)
                    doc['OCCI_Description']['mixins'] = var
            else:
                doc['OCCI_Description']['mixins'] = [mix_id]
        logger.debug("Associate mixin : Mixin associated with success")
        return db_docs,return_code['OK']
    else:
        logger.debug("Associate mixin : Mixin description problem")
        return list(),return_code['Not Found']

def associate_entities_to_mixins(mix_ids, db_docs):
    """
    Add a collection of mixins to entities
    Args:
        @param mix_ids: OCCI IDs of mixins
        @param db_docs: documents of the entities already contained in the database
    """

    for doc in db_docs:
        doc['OCCI_Description']['mixins'] = mix_ids
    logger.debug("Associate mixin : Mixin associated with success")
    return db_docs,return_code['OK']
