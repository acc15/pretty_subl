import sublime
import sublime_plugin
import traceback
import json
import xml.dom.minidom as md
import os
import re

class ForEachRegionTransform:

    default_params = { "indent": 4 }

    def format(self, text, params):
        for formatter in self.formatters:
            try:
                fmt = formatter(text, **params)
                print("formatted with " + formatter.__name__)
                return fmt           
            except:
                # traceback.print_exc()
                pass

    def run(self, edit, **params):
        regions = self.view.sel()
        
        if len(regions) == 0 or (len(regions) == 1 and regions[0].empty()):
            regions = [ sublime.Region(0, self.view.size()) ]
        
        merged_params = { **self.default_params, **params }
        for region in regions:
            text = self.view.substr(region)
            formatted = self.format(text, merged_params)
            if formatted is not None:
                self.view.replace(edit, region, formatted)


class JsonQuoteCommand(ForEachRegionTransform, sublime_plugin.TextCommand):
    formatters = [json_quote]

class UglyPrintCommand(ForEachRegionTransform, sublime_plugin.TextCommand):
    formatters = [uglify_xml, uglify_json]

class PrettyPrintCommand(ForEachRegionTransform, sublime_plugin.TextCommand):
    formatters = [prettify_xml, prettify_json]

#
# Formatters
#

def uglify_xml(value, **kwargs):
    xml_lines = get_xml_lines(value, lambda dom: dom.toxml())
    return "".join([line.strip() for line in xml_lines])

def prettify_xml(value, indent, **kwargs):
    xml_lines = get_xml_lines(value, lambda dom: dom.toprettyxml(indent = " " * indent))
    return os.linesep.join([line for line in xml_lines if line.strip()])

def uglify_json(value, **kwargs):
    parsed = json.loads(value)
    return json.dumps(parsed, ensure_ascii = False, separators = (',', ':'))

def prettify_json(value, indent, **kwargs):
    parsed = json.loads(value)
    if isinstance(parsed, str):
        return parsed
    return json.dumps(parsed, ensure_ascii = False, indent = indent)    

def json_quote(value, **kwargs):
    return json.dumps(value, ensure_ascii = False)

#
# XML utilities
#

xml_prolog_re = "^\\s*(<\\?\\s*xml.*\\?>)\\s*"

def get_xml_prolog(xml):
    m = re.search(xml_prolog_re, xml)
    return m.group(1) + "\n" if m else ""

def strip_xml_prolog(xml):
    m = re.search(xml_prolog_re, xml)
    return xml[:m.start()] + xml[m.end():] if m else xml

def get_xml_lines(xml, dom_formatter):
    dom = md.parseString(xml)
    formatted_xml = dom_formatter(dom)
    final_xml = get_xml_prolog(xml) + strip_xml_prolog(formatted_xml)
    return final_xml.splitlines()
