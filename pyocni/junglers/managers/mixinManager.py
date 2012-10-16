import pyocni.pyocni_tools.config as config
import pyocni.pyocni_tools.occi_Joker as joker


import pyocni.pyocni_tools.uuid_Generator as uuid_Generator
try:
    import simplejson as json
except ImportError:
    import json


from pyocni.pyocni_tools.config import return_code

# getting the Logger
logger = config.logger

class MixinManager:
    """

        Manager for Mixin documents on couch database

    """


    def get_filtered_mixins(self,jfilters,db_mixins):
        """
        Returns mixin documents matching the filter provided
        Args:
            @param jfilters: description of the mixin document to retrieve
            @param db_mixins: mixin descriptions that already exist in database
            @return : <list> OCCI mixin description contained inside of the mixin document
        """
        var = list()
        #Extract mixins descriptions from the dictionary
        try:
            for elem in db_mixins:
                for jfilter in jfilters:
                    ok = joker.filter_occi_description(elem,jfilter)
                    if ok is True:
                        var.append(elem)
                        logger.debug("===== Get_filtered_mixins: A Mixin document is found =====")
                        break

            return var,return_code['OK']

        except Exception as e:
            logger.error("===== Get_filtered_mixins:" + e.message+ " =====")
            return "An error has occurred",return_code['Internal Server Error']


    def register_mixins(self,creator,descriptions,db_occi_ids,db_occi_locs):

        """
        Add new mixins to the database
        Args:
            @param descriptions: OCCI mixin descriptions
            @param db_occi_ids: Existing Mixin IDs in database
            @param db_occi_locs: Existing Mixin locations in database
        """
        loc_res = list()
        resp_code = return_code['OK']
        for desc in descriptions:
            occi_id = joker.get_description_id(desc)
            ok_k = joker.verify_occi_uniqueness(occi_id,db_occi_ids)

            if ok_k is True:

                occi_loc = joker.make_category_location(desc)
                ok_loc = joker.verify_occi_uniqueness(occi_loc,db_occi_locs)

                if ok_loc is True:

                            jData = dict()
                            jData['_id'] = uuid_Generator.get_UUID()
                            jData['OCCI_Location']= occi_loc
                            jData['OCCI_Description']= desc
                            jData['OCCI_ID'] = occi_id
                            jData['Type']= "Mixin"
                            loc_res.append(jData)

                else:
                    message = "Location conflict, Mixin will not be created."
                    logger.error("===== Register Mixin : " + message + " =====")
                    resp_code = return_code['Conflict']
                    return list(),resp_code
            else:
                message = "This Mixin description already exists in document."
                logger.error(" ====== Register Mixin : " + message+ " =====")
                resp_code = return_code['Conflict']
                return list(),resp_code

        return loc_res,resp_code

    def update_OCCI_mixin_descriptions(self,new_data,db_data):
        """
        Updates the OCCI description field of the mixin which document OCCI_ID is equal to OCCI_ID contained in data
        (Should only be done by the creator of the mixin document)
        Args:

            @param new_data: Data containing the OCCI ID of the mixin and the new OCCI mixin description
            @param db_data: Data already contained in the database
            @return : <string>, return_code
        """
        to_update = list()
        resp_code = return_code['OK']

        for desc in new_data:
            occi_id = joker.get_description_id(desc)
            old_doc = joker.extract_doc(occi_id,db_data)

            if old_doc is not None:

                    problems,occi_description= joker.update_occi_category_description(old_doc['OCCI_Description'],desc)

                    if problems is True:
                        message = "Mixin OCCI description " + occi_id + " has not been totally updated."
                        logger.error("===== update_OCCI_mixin_descriptions: " + message + " ===== ")
                        return list(),return_code['Bad Request']

                    else:
                        message = "Mixin OCCI description " + occi_id + " has been updated successfully"
                        old_doc['OCCI_Description'] = occi_description
                        to_update.append(old_doc)
                        logger.debug("===== update_OCCI_mixin_descriptions: " + message + " ===== ")

            else:
                message = "Mixin document " + occi_id + " couldn\'t be found "
                logger.error("===== update_OCCI_mixin_descriptions: "+ message + " ===== ")
                return list(),return_code['Not Found']

        return to_update,resp_code

    def delete_mixin_documents(self,descriptions,db_categories,db_entities):
        """
        Delete mixin documents that is related to the scheme + term contained in the description provided
        Args:
            @param descriptions: OCCI description of the mixin document to delete
            @param db_categories: Category data already contained in the database
            @param db_entities: Entity data already contained in the database
        """

        mix_ref = list()
        res_code = return_code['OK']
        #Verify the existence of such kind document

        for desc in descriptions:
            occi_id = joker.get_description_id(desc)
            mixin_id_rev = joker.verify_exist_occi_id(occi_id,db_categories)

            if mixin_id_rev is not None:
                db_entities,dissociated = self.dissociate_entities_belonging_to_mixin(occi_id,db_entities)
                if dissociated is True:
                    mix_ref.append(mixin_id_rev)
                    event = "Mixin document " + occi_id + " is sent for delete "
                    logger.debug("===== Delete_mixin_documents : " + event + " =====")
                else:
                    event = "Unable to delete because this mixin document " + occi_id + " still has resources depending on it. "
                    logger.error(" ===== Delete_mixin_documents : " + event + " =====")
                    return list(),list(), return_code['Bad Request']
            else:
                event = "Could not find this mixin document " + occi_id
                logger.error("===== Delete_mixin_documents : " + event + " =====")
                return list(),list(), return_code['Bad Request']


        return mix_ref,db_entities,res_code

    def dissociate_entities_belonging_to_mixin(self, occi_id, db_entities):
        """
        Dissociates entities from a mixin
        Args:
            @param occi_id: OCCI ID of the mixin
            @param db_entities: Docs of the entities that could be having the mixin in their mixin collection
        """

        for item in db_entities:
            try:
                item['OCCI_Description']['mixins'].remove(occi_id)
            except ValueError as e:
                logger.debug("===== dissociate_entities_belonging_to_mixin " + e.message + " =====")
        return db_entities,True


