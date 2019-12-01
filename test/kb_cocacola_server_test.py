# -*- coding: utf-8 -*-
import os
import time
import unittest
import shutil
from configparser import ConfigParser

from kb_cocacola.kb_cocacolaImpl import kb_cocacola
from kb_cocacola.kb_cocacolaServer import MethodContext
from kb_cocacola.authclient import KBaseAuth as KBaseAuth

from kb_cocacola.Utils.CocacolaUtil import CocacolaUtil

from installed_clients.WorkspaceClient import Workspace

from installed_clients.AssemblyUtilClient import AssemblyUtil
from installed_clients.DataFileUtilClient import DataFileUtil
from installed_clients.ReadsUtilsClient import ReadsUtils

class kb_cocacolaTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # token = os.environ.get('KB_AUTH_TOKEN', None)
        cls.token = os.environ.get('KB_AUTH_TOKEN', None)
        config_file = os.environ.get('KB_DEPLOYMENT_CONFIG', None)
        cls.cfg = {}
        config = ConfigParser()
        config.read(config_file)
        for nameval in config.items('kb_cocacola'):
            cls.cfg[nameval[0]] = nameval[1]
        # Getting username from Auth profile for token
        authServiceUrl = cls.cfg['auth-service-url']
        auth_client = KBaseAuth(authServiceUrl)
        user_id = auth_client.get_user(cls.token)
        # WARNING: don't call any logging methods on the context object,
        # it'll result in a NoneType error
        cls.ctx = MethodContext(None)
        cls.ctx.update({'token': cls.token,
                        'user_id': user_id,
                        'provenance': [
                            {'service': 'kb_cocacola',
                             'method': 'please_never_use_it_in_production',
                             'method_params': []
                             }],
                        'authenticated': 1})
        cls.wsURL = cls.cfg['workspace-url']
        cls.wsClient = Workspace(cls.wsURL)
        cls.serviceImpl = kb_cocacola(cls.cfg)
        cls.scratch = cls.cfg['scratch']
        cls.callback_url = os.environ['SDK_CALLBACK_URL']
        suffix = int(time.time() * 1000)
        cls.wsName = "test_kb_cocacola_" + str(suffix)
        # ret = cls.wsClient.create_workspace({'workspace': cls.wsName})  # noqa

        cls.ws_info = cls.wsClient.create_workspace({'workspace': cls.wsName})  # noqa
        cls.dfu = DataFileUtil(os.environ['SDK_CALLBACK_URL'], token=cls.token)
        cls.ru = ReadsUtils(os.environ['SDK_CALLBACK_URL'], token=cls.token)
        cls.au = AssemblyUtil(os.environ['SDK_CALLBACK_URL'], token=cls.token)
        cls.cocacola_runner = CocacolaUtil(cls.cfg)
        cls.prepare_data()


    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'wsName'):
            cls.wsClient.delete_workspace({'workspace': cls.wsName})
            print('Test workspace was deleted')


    @classmethod
    def prepare_data(cls):
        """
        Lets put everything on workspace
        """
        # building Assembly
        #
        assembly_filename = 'small_arctic_assembly.fa'
        cls.assembly_filename_path = os.path.join(cls.scratch, assembly_filename)
        shutil.copy(os.path.join("data", assembly_filename), cls.assembly_filename_path)

        # from scratch upload to workspace
        assembly_params = {
            'file': {'path': cls.assembly_filename_path},
            'workspace_name': cls.ws_info[1],
            'assembly_name': 'MyAssembly'
        }

        # puts assembly object onto shock
        cls.assembly_ref = cls.au.save_assembly_from_fasta(assembly_params)


        #
        # READS 1
        # building Interleaved library
        pe1_reads_filename = 'lib1.oldstyle.fastq'
        pe1_reads_path = os.path.join(cls.scratch, pe1_reads_filename)

        # gets put on scratch. "work/tmp" is scratch
        shutil.copy(os.path.join("data", pe1_reads_filename), pe1_reads_path)

        int1_reads_params = {
            'fwd_file': pe1_reads_path,
            'sequencing_tech': 'Unknown',
            'wsname': cls.ws_info[1],
            'name': 'MyInterleavedLibrary1',
            'interleaved': 'true'
        }

        #from scratch upload to workspace

        cls.int1_oldstyle_reads_ref = cls.ru.upload_reads(int1_reads_params)['obj_ref']
        print("cls.int1_oldstyle_reads_ref***")
        print(str(cls.int1_oldstyle_reads_ref))

        #READS 2
        #building Interleaved library
        pe2_reads_filename = 'lib2.oldstyle.fastq'
        pe2_reads_path = os.path.join(cls.scratch, pe2_reads_filename)

        # gets put on scratch. "work/tmp" is scratch
        shutil.copy(os.path.join("data", pe2_reads_filename), pe2_reads_path)

        int2_reads_params = {
            'fwd_file': pe2_reads_path,
            'sequencing_tech': 'Unknown',
            'wsname': cls.ws_info[1],
            'name': 'MyInterleavedLibrary2',
            'interleaved': 'true'
        }

        #from scratch upload to workspace
        cls.int2_oldstyle_reads_ref = cls.ru.upload_reads(int2_reads_params)['obj_ref']

    def getWsClient(self):
        return self.__class__.wsClient

    def getWsName(self):
        return self.ws_info[1]

    def getImpl(self):
        return self.__class__.serviceImpl

    def getContext(self):
        return self.__class__.ctx


    def test_run_cocacola_multiple_read_input(self):
        method_name = 'test_run_cocacola_multiple_read_input'
        print ("\n=================================================================")
        print ("RUNNING "+method_name+"()")
        print ("=================================================================\n")

        # cocacola should run to completion here
        ret = self.getImpl().run_kb_cocacola(self.getContext(),
                                            {'workspace_name': self.getWsName(),
                                             'assembly_ref': self.assembly_ref,
                                             'read_mapping_tool': 'minimap2',
                                             'min_contig_length': 3000,
                                             'contig_split_size': 10000,
                                             'contig_split_overlap': 0,
                                             'kmer_size': 4,
                                             'binned_contig_name': 'cocacola_bin_obj',
                                             'reads_list': [self.int1_oldstyle_reads_ref, self.int2_oldstyle_reads_ref] })


    def test_run_cocacola_bowtie2_default_mapping_input(self):
        method_name = 'test_run_cocacola_bowtie2_default_mapping_input'
        print ("\n=================================================================")
        print ("RUNNING "+method_name+"()")
        print ("=================================================================\n")

        # cocacola should run to completion here
        ret = self.getImpl().run_kb_cocacola(self.getContext(),
                                            {'workspace_name': self.getWsName(),
                                             'assembly_ref': self.assembly_ref,
                                             'read_mapping_tool': 'bowtie2_default',
                                             'min_contig_length': 3000,
                                             'contig_split_size': 10000,
                                             'contig_split_overlap': 0,
                                             'kmer_size': 4,
                                             'binned_contig_name': 'cocacola_bin_obj',
                                             'reads_list': [self.int1_oldstyle_reads_ref] })

    def test_run_cocacola_bowtie2_very_sensitive_mapping_input(self):
        method_name = 'test_run_cocacola_bowtie2_very_sensitive_mapping_input'
        print ("\n=================================================================")
        print ("RUNNING "+method_name+"()")
        print ("=================================================================\n")

        # cocacola should run to completion here
        ret = self.getImpl().run_kb_cocacola(self.getContext(),
                                            {'workspace_name': self.getWsName(),
                                             'assembly_ref': self.assembly_ref,
                                             'read_mapping_tool': 'bowtie2_very_sensitive',
                                             'min_contig_length': 3000,
                                             'contig_split_size': 10000,
                                             'contig_split_overlap': 0,
                                             'kmer_size': 4,
                                             'binned_contig_name': 'cocacola_bin_obj',
                                             'reads_list': [self.int1_oldstyle_reads_ref] })

    def test_run_cocacola_hisat2_mapping_input(self):
        method_name = 'test_run_cocacola_hisat2_mapping_input'
        print ("\n=================================================================")
        print ("RUNNING "+method_name+"()")
        print ("=================================================================\n")

        # cocacola should run to completion here
        ret = self.getImpl().run_kb_cocacola(self.getContext(),
                                            {'workspace_name': self.getWsName(),
                                             'assembly_ref': self.assembly_ref,
                                             'read_mapping_tool': 'hisat2',
                                             'min_contig_length': 3000,
                                             'contig_split_size': 10000,
                                             'contig_split_overlap': 0,
                                             'kmer_size': 4,
                                             'binned_contig_name': 'cocacola_bin_obj',
                                             'reads_list': [self.int1_oldstyle_reads_ref] })

    def test_run_cocacola_bbmap_mapping_input(self):
        method_name = 'test_run_cocacola_bbmap_mapping_input'
        print ("\n=================================================================")
        print ("RUNNING "+method_name+"()")
        print ("=================================================================\n")

        # cocacola should run to completion here
        ret = self.getImpl().run_kb_cocacola(self.getContext(),
                                            {'workspace_name': self.getWsName(),
                                             'assembly_ref': self.assembly_ref,
                                             'read_mapping_tool': 'bbmap',
                                             'min_contig_length': 3000,
                                             'contig_split_size': 10000,
                                             'contig_split_overlap': 0,
                                             'kmer_size': 4,
                                             'binned_contig_name': 'cocacola_bin_obj',
                                             'reads_list': [self.int1_oldstyle_reads_ref] })

    def test_run_cocacola_minimap2_mapping_input(self):
        method_name = 'test_run_cocacola_minimap2_mapping_input'
        print ("\n=================================================================")
        print ("RUNNING "+method_name+"()")
        print ("=================================================================\n")

        # cocacola should run to completion here
        ret = self.getImpl().run_kb_cocacola(self.getContext(),
                                            {'workspace_name': self.getWsName(),
                                             'assembly_ref': self.assembly_ref,
                                             'read_mapping_tool': 'minimap2',
                                             'min_contig_length': 3000,
                                             'contig_split_size': 10000,
                                             'contig_split_overlap': 0,
                                             'kmer_size': 4,
                                             'binned_contig_name': 'cocacola_bin_obj',
                                             'reads_list': [self.int1_oldstyle_reads_ref] })

    def test_run_cocacola_bwa_mapping_input(self):
        method_name = 'test_run_cocacola_bwa_mapping_input'
        print ("\n=================================================================")
        print ("RUNNING "+method_name+"()")
        print ("=================================================================\n")

        # cocacola should run to completion here
        ret = self.getImpl().run_kb_cocacola(self.getContext(),
                                            {'workspace_name': self.getWsName(),
                                             'assembly_ref': self.assembly_ref,
                                             'read_mapping_tool': 'bwa',
                                             'min_contig_length': 3000,
                                             'contig_split_size': 10000,
                                             'contig_split_overlap': 0,
                                             'kmer_size': 4,
                                             'binned_contig_name': 'cocacola_bin_obj',
                                             'reads_list': [self.int1_oldstyle_reads_ref] })
