import os
from lxml.etree import SubElement, QName
import pandas as pd

class Tools:
    def __init__(self, id):
        self.ns = {"z": "http://purl.org/net/xbiblio/csl"}
        df = pd.read_excel(os.path.dirname(os.path.abspath(__file__))+"/../input/config.xlsx")[["variable", id]].fillna("")
        self.config = dict(zip(df["variable"],df[id]))
    
    def appendchild(self, parent, tag, text=None, attribs={}):
        child = SubElement(parent, tag)
        if text is not None:
            child.text = text
        for a in attribs:
            child.attrib[a] = attribs[a]
        parent.insert(-1, child)
        return child
        
    def insertchild(self, index, parent, tag, text=None, attribs={}):
        child = SubElement(parent, tag)
        if text is not None:
            child.text = text
        for a in attribs:
            child.attrib[a] = attribs[a]
        parent.insert(index, child)
        return child
    
    def qname(self, v):
        return QName("http://www.w3.org/XML/1998/namespace", v)
    
    def localize(self, element, language="ja"):
        if "macro" in element.attrib:
            element.attrib["macro"] = element.attrib["macro"]+"-"+language
            for a in element.attrib:
                if a in ["prefix", "suffix"]:
                    element.attrib.pop(a)
        for c in element.getchildren():
            self.localize(c)
    
    def render(self, d, parent, previous=None, after=None, where=None, path=None):
        if path is not None:
            parent = self.child(parent, path)
            
        tag = d.get("tag", None)
        attrib = d.get("attrib", {})
        text = d.get("text", None)
        children = d.get("children", [])
        element = None
        
        if where is not None:
            index = where
        elif after is not None:
            index = parent.getchildren().index(after)
        elif previous is not None:
            index = previous.getparent().getchildren().index(previous)+1
        else:
            try:
                previous = parent.getchildren()[len(parent.getchildren())-1]
                index = parent.getchildren().index(previous)+1
            except:
                index = 0
        
        if tag is not None:
            element = SubElement(parent, tag)
            parent.insert(index, element)
            
            if text is not None:
                setattr(element, "text", text)
                
            for key in attrib:
                value = attrib[key]
                element.attrib[key] = value
            
            for child in children:
                self.render(child, element)
        return element
    
    def child(self, parent, path):
        c = parent.xpath(path, namespaces=self.ns)
        if len(c)>0:
            return c[0]
        else:
            return None