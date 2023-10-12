import os, copy, datetime, pytz
from lxml import etree as ET
from lxml.etree import SubElement, QName
from .tools import Tools

from .processor import Processor

class Base:
    def __init__(self, ids, name, language, multilingual):
        self.id = ids[0]
        self.input = "input/chicago-author-date.csl"
        self.output = "output/chicago-author-date-"+self.id+".csl"
        
        self.tools = Tools(self.id)
        
        #basic settings
        self.sortkey = "name-kana"
        self.ns = self.tools.ns
        
        #basic info
        self.journalname = name
        self.language = language
        
        #xml bases
        parser = ET.XMLParser(remove_blank_text=True)
        self.tree = ET.parse(self.input, parser)
        self.root = self.tree.getroot()
        self.info = self.tree.findall('z:info', self.ns)[0]
        self.citation = self.tree.findall('z:citation', self.ns)[0]
        self.bibliography = self.tree.findall('z:bibliography', self.ns)[0]
        self.bibliography.attrib.pop("subsequent-author-substitute")
        
        self.root.attrib["page-range-format"] = "expanded"
        
        # retrieve macro list
        self.macros = self.getmacros()
        self.jamacros = self.getmacrosja()
        
        """
        Bibliography settings
        """
        # Add sorting key: kana-name
        if multilingual:
            sort = self.bibliography.xpath("z:sort", namespaces=self.ns)[0]
            key = SubElement(sort, "key")
            key.attrib["variable"] = self.sortkey
            sort.insert(0, key)
        
        """
        Split in two languages
        """
        # Add ja bibliography layouts
        self.bibliographylayout = self.tree.findall('z:bibliography/z:layout', self.ns)[0]
        if multilingual:
            self.bibliographylayoutja = copy.deepcopy(self.bibliographylayout)
            self.bibliographylayoutja.attrib["locale"] = "ja"
            idx = self.bibliography.getchildren().index(self.bibliographylayout)
            self.bibliography.insert(idx, self.bibliographylayoutja)
            for child in self.bibliographylayoutja.getchildren():
                self.tools.localize(child)
        
        """
        Citation settings
        """
        self.citationlayout = self.tree.findall('z:citation/z:layout', self.ns)[0]
        if multilingual:
            self.citationlayoutja = copy.deepcopy(self.citationlayout)
            self.citationlayoutja.attrib["locale"] = "ja"
            idx = self.citation.getchildren().index(self.citationlayout)
            self.citation.insert(idx, self.citationlayoutja)
            for child in self.citationlayoutja.getchildren():
                self.tools.localize(child)
            
        # Citation main settings
        self.citation.attrib["et-al-min"] = "3"
        self.citation.attrib["disambiguate-add-year-suffix"] = "false"
        self.citation.attrib["disambiguate-add-names"] = "false"
        self.citation.attrib["disambiguate-add-givenname"] = "false"
        
        """
        Edit metadata
        """
        self.setmetadata()
        
        """ 
        Create locales
        """
        if multilingual:
            localeja = SubElement(self.info.getparent(), "locale")
            terms = SubElement(localeja, "terms")
            localeja.attrib[self.tools.qname("lang")] = "ja"
            idx = self.info.getparent().getchildren().index(self.info)+1
            self.info.getparent().insert(idx, localeja)
            localeja.insert(0, terms)
            
            #Insert locale terms
            self.tools.appendchild(terms, "term", "頁", {"name": "page", "form": "long"})
            self.tools.appendchild(terms, "term", "巻", {"name": "volume", "form": "short"})
            self.tools.appendchild(terms, "term", "号", {"name": "issue", "form": "short"})
            self.tools.appendchild(terms, "term", "訳", {"name": "translator", "form": "short"})
            self.tools.appendchild(terms, "term", "編訳", {"name": "editortranslator", "form": "short"})
            self.tools.appendchild(terms, "term", "アクセス", {"name": "accessed"})
        
        if multilingual:
            #Process Japanese
            Processor(ids[1], self.jamacros, self.citationlayoutja, self.bibliographylayoutja).process()
            
        #Process English
        Processor(self.id, self.macros, self.citationlayout, self.bibliographylayout).process()
    
    def getmacros(self):
        m = self.tree.findall('z:macro', self.ns)
        m = {x.attrib["name"]:x for x in m}
        return m
    
    def getmacrosja(self):
        macros = {}
        for i in self.macros:
            macro = self.macros[i]
            parent= macro.getparent()
            index = parent.getchildren().index(macro)+1
            jm = copy.deepcopy(macro)
            mkey = jm.attrib["name"]
            jm.attrib["name"] = mkey+"-ja"
            parent.insert(index, jm)
            macros[mkey] = jm
        return macros
    
    def setmetadata(self):
        """
        Add my contributions
        """
        last_contributor = self.info.findall("z:contributor", self.ns)[-1]
        moi = {
            "tag": "contributor", "children": [
                {"tag": "name", "text": "Fanantenana Rianasoa Andriariniaina"},
                {"tag": "uri", "text": "https://orcid.org/0000-0002-8665-0922"},
            ]
        }
        self.tools.render(moi, self.info, last_contributor)
        
        """
        Add title
        """
        for title in self.tree.findall('z:info/z:title', self.ns):
            title.text = self.journalname+" ("+self.language+")"
        
        """
        Add id
        """
        for id in self.tree.findall('z:info/z:id', self.ns):
            id.text = "http://www.zotero.org/styles/chicago-author-date"+"-"+self.id
        
        """
        Add summary
        """
        for summary in self.tree.findall('z:info/z:summary', self.ns):
            summary.text = summary.text+" - Edited for "+self.journalname+" ("+self.language+")"
        
        """
        Add updated date
        """
        up = self.tools.child(self.info, "z:updated")
        up.text = datetime.datetime.now().astimezone().replace(microsecond=0).isoformat()
      
    def create(self):
        os.makedirs("output", exist_ok=True)
        self.tree.write(self.output, pretty_print=True, xml_declaration=True, encoding="UTF-8")