import sublime
import sublime_plugin
import traceback
import json
import xml.dom.minidom as md
import os
import re

class ForEachRegionTransform:

    default_params = { "indent": 4 }

    def __init__(self, view):
        self.view = view
        self.formatters = [ getattr(self, m) for m in dir(self) if m.startswith("format_") ]

    def transform(self, value, params):
        merged_params = { **self.default_params, **params }
        for fmt in self.formatters:
            try:
                fmt_value = fmt(value, **merged_params)
                print("formatted as " + fmt.__name__[7:])
                return fmt_value
            except:
                # traceback.print_exc()
                pass
        return None

    def run(self, edit, **kwargs):
        selection = self.view.sel()
        regions = selection
        
        if len(regions) == 0 or (len(regions) == 1 and regions[0].empty()):
            regions = [ sublime.Region(0, self.view.size()) ]
        
        for region in regions:
            text = self.view.substr(region)
            decoded = self.transform(text, kwargs)
            if decoded is not None:
                self.view.replace(edit, region, decoded)


class JsonQuoteCommand(ForEachRegionTransform, sublime_plugin.TextCommand):
    def format_json(self, value, **kwargs):
        return json.dumps(value, ensure_ascii = False)

class UglyPrintCommand(ForEachRegionTransform, sublime_plugin.TextCommand):
    def format_xml(self, value, **kwargs):
        xml = XmlUtils.format_xml(value, lambda dom: dom.toxml())
        return "".join([line.strip() for line in xml.splitlines()])

    def format_json(self, value, **kwargs):
        parsed = json.loads(value)
        return json.dumps(parsed, ensure_ascii = False, separators = (',', ':'))

class PrettyPrintCommand(ForEachRegionTransform, sublime_plugin.TextCommand):
    def format_xml(self, value, indent):
        xml = XmlUtils.format_xml(value, lambda dom: dom.toprettyxml(indent = " " * indent))
        return os.linesep.join([s for s in xml.splitlines() if s.strip()])

    def format_json(self, value, indent):
        parsed = json.loads(value)
        if isinstance(parsed, str):
            return parsed
        return json.dumps(parsed, ensure_ascii = False, indent = indent)
        

class XmlUtils:
    xml_prolog_re = "^\\s*(<\\?\\s*xml.*\\?>)\\s*"

    def get_xml_prolog(xml):
        m = re.search(xml_prolog_re, xml)
        return m.group(1) + "\n" if m else ""

    def strip_xml_prolog(xml):
        m = re.search(xml_prolog_re, xml)
        return xml[:m.start()] + xml[m.end():] if m else xml

    def format_xml(xml, dom_formatter):
        dom = md.parseString(xml)
        formatted_xml = dom_formatter(dom)
        return get_xml_prolog(xml) + strip_xml_prolog(formatted_xml)
