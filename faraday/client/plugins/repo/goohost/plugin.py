#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Faraday Penetration Test IDE
Copyright (C) 2013  Infobyte LLC (http://www.infobytesec.com/)
See the file 'doc/LICENSE' for the license information
'''

from __future__ import with_statement
from faraday.client.plugins import core
import socket
import sys
import re
import os

current_path = os.path.abspath(os.getcwd())

__author__ = "Francisco Amato"
__copyright__ = "Copyright (c) 2013, Infobyte LLC"
__credits__ = ["Francisco Amato"]
__license__ = ""
__version__ = "1.0.0"
__maintainer__ = "Francisco Amato"
__email__ = "famato@infobytesec.com"
__status__ = "Development"


class GoohostParser(object):
    """
    The objective of this class is to parse an xml file generated by the goohost tool.

    TODO: Handle errors.
    TODO: Test goohost output version. Handle what happens if the parser doesn't support it.
    TODO: Test cases.

    @param goohost_scantype You could select scan type ip, mail or host
    """

    def __init__(self, output, goohost_scantype):

        self.items = []
        lines = filter(None, output.split('\n'))
        for line in lines:
            if goohost_scantype == 'ip':
                data = line.split()
                item = {'host': data[0], 'ip': data[1]}
                self.add_host_info_to_items(item['ip'], item['host'])
            elif goohost_scantype == 'host':
                data = line.strip()
                item = {'host': data, 'ip': self.resolve(data)}
                self.add_host_info_to_items(item['ip'], item['host'])
            else:
                item = {'data': line}

    def resolve(self, host):
        try:
            return socket.gethostbyname(host)
        except:
            pass
        return host

    def add_host_info_to_items(self, ip_address, hostname):
        data = {}
        exists = False
        for item in self.items:
            if ip_address in item['ip']:
                item['hosts'].append(hostname)
                exists = True

        if not exists:
            data['ip'] = ip_address
            data['hosts'] = [hostname]
            self.items.append(data)


class GoohostPlugin(core.PluginBase):
    """
    Example plugin to parse goohost output.
    """

    def __init__(self):
        core.PluginBase.__init__(self)
        self.id = "Goohost"
        self.name = "Goohost XML Output Plugin"
        self.plugin_version = "0.0.1"
        self.version = "v.0.0.1"
        self.options = None
        self._current_output = None
        self._current_path = None
        self._command_regex = re.compile(
            r'^(sudo goohost\.sh|goohost\.sh|sh goohost\.sh|\.\/goohost\.sh).*?')
        self.host = None

        global current_path
        self.output_path = None
        self._command_string = None

    def parseOutputString(self, output, debug=False):
        """
        This method will check if the import was made through the console or by importing a Goohost report.

        Import from Console:The method will take the path of the report generated by Goohost from the output the shell sends and will read
        the information from the txt where it expects it to be present.

        Import from Report: The method receives the output of the txt report as parameter.

        self.scantype defines the method used to generate the Goohost report

        NOTE: if 'debug' is true then it is being run from a test case and the
        output being sent is valid.
        """

        if self._command_string:
            # Import from console
            self.scantype = self.define_scantype_by_command(self._command_string)
            report_output = output
            output = self.read_output_file(report_output)
        else:
            # Import from report
            self.scantype = self.define_scantype_by_output(output)

        if debug:
            parser = GoohostParser(output, self.scantype)
        else:
            parser = GoohostParser(output, self.scantype)
            if self.scantype == 'host' or self.scantype == 'ip':
                for item in parser.items:
                    h_id = self.createAndAddHost(
                        item['ip'],
                        hostnames=item['hosts'])

        del parser

    def processCommandString(self, username, current_path, command_string):
        """
        Set output path for parser...
        """
        self._current_path = current_path
        self._command_string = command_string

    def define_scantype_by_command(self, command):
        method_regex = re.compile(r'-m (mail|host|ip)')
        method = method_regex.search(command)
        if method:
            return method.group(1)

        return 'host'

    def define_scantype_by_output(self, output):
        lines = output.split('\n')
        line = lines[0].split(' ')

        if len(line) == 1:
            return 'host'
        elif len(line) == 2:
            return 'ip'

    def read_output_file(self, report_path):
        mypath = re.search("Results saved in file (\S+)", report_path)
        if not mypath:
            return False
        else:
            self.output_path = self._current_path + "/" + mypath.group(1)
            if not os.path.exists(self.output_path):
                return False
            with open(self.output_path, 'r') as report:
                output = report.read()

            return output


def createPlugin():
    return GoohostPlugin()

if __name__ == '__main__':
    with open('/home/javier/Plugins/goohost/report-10071-google.com.txt','r') as report:
        output = report.read()
    parser = GoohostPlugin()
    parser.parseOutputString(output)
    for item in parser.items:
        if item.status == 'up':
            print item