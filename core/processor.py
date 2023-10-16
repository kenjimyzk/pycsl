import copy
from lxml.etree import SubElement
from .tools import Tools

class Processor:
    def __init__(self, root, id, mainconfig, macros, citationlayout, bibliographylayout):
        self.root = root
        self.macros = macros
        self.tools = Tools(id)
        self.config = self.tools.config
        self.mainconfig = mainconfig
        self.citationlayout = citationlayout
        self.bibliographylayout = bibliographylayout
        self.langsuffix = "-"+id.split("-")[1] if len(id.split("-"))>1 else ""
        
        # Set locale style options
        locale = self.root.xpath("z:locale[@xml:lang='"+self.langsuffix.replace("-", "")+"']", namespaces=self.tools.ns)[0]
        
        self.tools.insertchild(0, locale, "style-options", None, {"punctuation-in-quote": self.tools.config.get("a-punctuation-in-quote", "false")})
        
        # Page delimiter settings
        terms = self.root.xpath("z:locale[@xml:lang='"+self.langsuffix.replace("-", "")+"']/z:terms", namespaces=self.tools.ns)[0]
        self.tools.appendchild(terms, "term", self.config.get("a-page-range-delimiter", "-"), {"name": "page-range-delimiter"})
        
        # Remove -en for default
        if "-en" in self.langsuffix:
            self.langsuffix=""
        
        
    def process(self):
        self.setbibliography()
        self.setcitation()
    
    def setcitation(self):
        config = self.config
        """
        Citation layout
        """
        # all brackets
        self.citationlayout.attrib["prefix"] = self.mainconfig.get("bracket-left", "（")
        self.citationlayout.attrib["suffix"] = self.mainconfig.get("bracket-right", "）")
        
        # between author/date 
        group = self.citationlayout.xpath("z:group/z:choose/z:if/z:group", namespaces=self.tools.ns)[0]
        group.attrib["delimiter"] = config.get("c-name-date-delimiter", ", ")
        
        #between author/n.d
        group = self.citationlayout.xpath("z:group/z:choose/z:else/z:group", namespaces=self.tools.ns)[0]
        group.attrib["delimiter"] = config.get("c-name-date-delimiter", ", ")
        
        """
        Separators and "and"
        """
        
        contributors = self.macros.get("contributors-short", None)
        name = contributors.xpath("z:names/z:name", namespaces=self.tools.ns)[0]
        name.attrib["delimiter"] = config.get("c-name-delimiter", "")
        name.attrib["and"] = config.get("c-and-form", "")
        
        """
        Set page number
        """
        locator = self.macros.get("point-locators", None)
        
        # Address inverted
        locatortext = locator.xpath("z:choose/z:if/z:text", namespaces=self.tools.ns)[0]
        if config.get("c-invert-page-label", False):
            locatortext.getparent().insert(0, locatortext)  
        
        
        labelgroup = locator.xpath("z:choose/z:if/z:choose", namespaces=self.tools.ns)[0]
        # Remove label if not needed
        if config.get("c-page-label-form", "") == "":
            labelgroup.getparent().remove(labelgroup)
        # Or add label to page
        else:
            # if volume
            volumegroup = labelgroup.xpath("z:else-if", namespaces=self.tools.ns)[0]
            pagelabel = self.tools.appendchild(volumegroup, "label", None, {"variable": "locator"})
            
            # if no volume
            ifpage = self.tools.appendchild(labelgroup, "else", None, {})
            pagelabel = self.tools.appendchild(ifpage, "label", None, {"variable": "locator"})
            
            # Add suffix
            labels = locator.xpath(".//z:label", namespaces=self.tools.ns)
            for label in labels:
                label.attrib["form"] = config.get("c-page-label-form", "long")
                label.attrib["suffix"] = config.get("c-page-label-suffix", " ")
                
        # between date and page
        group = self.citationlayout.xpath("z:group", namespaces=self.tools.ns)[0]
        group.attrib["delimiter"] = config.get("c-date-page-delimiter", ", ")
        
        # et-al setting
        citation = self.citationlayout.getparent()
        if config.get("c-et-al-subsequent", False):
            citation.attrib.pop("et-al-min")
            citation.attrib.pop("et-al-use-first")
            citation.attrib["et-al-subsequent-min"] = "3"
            citation.attrib["et-al-subsequent-use-first"] = "1"
        
        # delimiter-precedes-last
        if config.get("c-delimiter-precedes-last", False):
            citation.attrib["delimiter-precedes-last"] = "always"
        else:
            citation.attrib["delimiter-precedes-last"] = "never"
        
        """
        Dates
        """
        # Original date
        dateintext = self.macros.get("date-in-text", None)
        group = dateintext.xpath("z:choose/z:if/z:group", namespaces=self.tools.ns)[0]
        group.attrib["delimiter"] = ""
        originaldate = group.xpath("z:date[@variable='original-date']", namespaces=self.tools.ns)[0]
        originaldate.attrib["prefix"] = config.get("c-original-date-left", "")
        originaldate.attrib["suffix"] = config.get("c-original-date-right", "=")
        originaldate.attrib.pop("form")
        originaldate.attrib.pop("date-parts")
        self.tools.appendchild(originaldate, "date-part", None, {"name": "year"})
        
        
    def setbibliography(self):
        """
        Bibliography layout
        """
        config = self.config
        
        # Layout order
        containercontributor = self.bibliographylayout.xpath("z:text[@macro='container-contributors"+self.langsuffix+"']", namespaces=self.tools.ns)[0]
        idx = self.bibliographylayout.getchildren().index(containercontributor)-1
        self.bibliographylayout.insert(idx, containercontributor)
        
        # Move locator chapter after issue
        issue = self.bibliographylayout.xpath("z:text[@macro='issue"+self.langsuffix+"']", namespaces=self.tools.ns)[0]
        locatorschapter = self.bibliographylayout.xpath("z:text[@macro='locators-chapter"+self.langsuffix+"']", namespaces=self.tools.ns)[0]
        idx = issue.getparent().getchildren().index(locatorschapter)
        issue.getparent().insert(idx, issue)
                
        # Remove delimiters
        group = self.bibliographylayout.xpath("z:group", namespaces=self.tools.ns)[0]
        group.attrib.pop("delimiter")
        self.bibliographylayout.attrib.pop("suffix")
        
        # Add period before access
        period = SubElement(self.bibliographylayout, "text")
        period.attrib["value"] = config.get("b-final-punctuation", ". ")
        self.bibliographylayout.insert(-2, period)
        
        """
        Contributors
        """
        
        contributors = self.macros.get("contributors", None)
        
        # Change delimiters
        name = contributors.xpath("z:group/z:names/z:name", namespaces=self.tools.ns)[0]
        name.attrib["and"] = config.get("b-and-form", "")
        name.attrib["delimiter"] = config.get("b-name-delimiter", "・")
        name.attrib["sort-separator"] = config.get("b-name-sort-separator", ",")
        name.attrib["delimiter-precedes-last"] = config.get("b-delimiter-precedes-last", "never")
        if config.get("b-name-initialize-with", "")!="":
            name.attrib["initialize-with"] = config.get("b-name-initialize-with", "")
            name.attrib["initialize"] = config.get("b-name-initialize", "")
        if config.get("b-contributor-name-as-sort-order", "")!="":
            name.attrib["name-as-sort-order"] = config.get("b-contributor-name-as-sort-order", "first")
        
        # Label
        label = contributors.xpath("z:group/z:names/z:label", namespaces=self.tools.ns)[0]
        label.attrib["prefix"] = ""
        
        # Split names with delimiters
        if config.get("b-name-part-delimiter", "")!="":
            self.tools.splitname(name, config.get("b-name-part-delimiter", ""))
        
        """
        Container contributors
        """
        contributors = self.macros.get("container-contributors", None)
        group = contributors.xpath("z:choose/z:if/z:group", namespaces=self.tools.ns)[0]
        labels = contributors.xpath("z:choose/z:if/z:group/z:names/z:label", namespaces=self.tools.ns)
        names = contributors.xpath("z:choose/z:if/z:group/z:names/z:name", namespaces=self.tools.ns)
        
        group.attrib["prefix"] = ""
        
        for label in labels:
            label.attrib["form"] = "short"
            idx = len(label.getparent())
            label.getparent().insert(idx, label)
        
        for name in names:
            name.attrib["and"] = config.get("b-and-form", "")
            name.attrib["delimiter"] = config.get("b-name-delimiter", "・")
            name.attrib["sort-separator"] = config.get("b-name-sort-separator", ",")
            name.attrib["delimiter-precedes-last"] = config.get("b-delimiter-precedes-last", "never")
            if config.get("b-container-contributor-name-as-sort-order", "")!="":
                name.attrib["name-as-sort-order"] = config.get("b-container-contributor-name-as-sort-order", "first")
        
        # Remove prefix from container-title to container-contributor suffix
        title = self.bibliographylayout.xpath("z:text[@macro='container-title"+self.langsuffix+"']", namespaces=self.tools.ns)[0]
        title.attrib["prefix"] = ""
        
        authors = self.bibliographylayout.xpath("z:text[@macro='container-contributors"+self.langsuffix+"']", namespaces=self.tools.ns)[0]
        authors.attrib["suffix"] = config.get("b-book-authors-suffix", ". ")
        
        # Move container-prefix="in" to contributors from title
        title = self.macros.get('container-title', None)
        authors = self.macros.get('container-contributors', None).xpath("z:choose/z:if/z:group", namespaces=self.tools.ns)[0]
        prefix = title.xpath("z:choose/z:if/z:text[@macro='container-prefix']", namespaces=self.tools.ns)[0]
        prefix.attrib["prefix"] = ". "
        prefix.attrib["suffix"] = ""
        authors.attrib["delimiter"] = " "
        authors.insert(0, prefix)
        
        # Format names and labels
        nameslist = self.macros.get('container-contributors', None).xpath("z:choose/z:if/z:group/z:names", namespaces=self.tools.ns)
        namelist = self.macros.get('container-contributors', None).xpath("z:choose/z:if/z:group/z:names/z:name", namespaces=self.tools.ns)
        labels = self.macros.get('container-contributors', None).xpath("z:choose/z:if/z:group/z:names/z:label", namespaces=self.tools.ns)
        
        for names in nameslist:
            if config.get("b-container-contributors-left", "")!="":
                names.attrib["prefix"] = config.get("b-container-contributors-left", "")
            if config.get("b-container-contributors-right", "")!="":
                names.attrib["suffix"] = config.get("b-container-contributors-right", "")
        
        for name in namelist:
            name.attrib["and"] = config.get("b-and-form", "")
            name.attrib["delimiter"] = config.get("b-name-delimiter", "・")
            name.attrib["sort-separator"] = config.get("b-name-sort-separator", ",")
            name.attrib["delimiter-precedes-last"] = config.get("b-delimiter-precedes-last", "never")
            if config.get("b-name-initialize-with", "")!="":
                name.attrib["initialize-with"] = config.get("b-name-initialize-with", "")
                name.attrib["initialize"] = config.get("b-name-initialize", "")
            
            if config.get("b-container-contributor-name-as-sort-order", "")!="":
                name.attrib["name-as-sort-order"] = config.get("b-container-contributor-name-as-sort-order", "first")
        
        for label in labels:
            label.attrib["prefix"] = config.get("b-contributor-label-left", " (")
            label.attrib["suffix"] = config.get("b-contributor-label-right", ")")
                
        """
        Secondary contributors
        """
        secondarycontributors = self.bibliographylayout.xpath("z:text[@macro='secondary-contributors"+self.langsuffix+"']", namespaces=self.tools.ns)[0]
        secondarycontributors.attrib["suffix"] = config.get("b-secondary-contributor-label-right", ",")
        
        # Remove prefix
        authors = self.bibliographylayout.xpath("z:text[@macro='secondary-contributors"+self.langsuffix+"']", namespaces=self.tools.ns)[0]
        if "prefix" in authors.attrib:
            authors.attrib.pop("prefix")
        
        names = self.macros.get('secondary-contributors', None).xpath("z:choose/z:if/z:group/z:names", namespaces=self.tools.ns)[0]
        namelist = self.macros.get('secondary-contributors', None).xpath("z:choose/z:if/z:group/z:names/z:name", namespaces=self.tools.ns)
        labels = self.macros.get('secondary-contributors', None).xpath("z:choose/z:if/z:group/z:names/z:label", namespaces=self.tools.ns)
        
        if config.get("b-secondary-contributors-left", "")!="":
            names.attrib["prefix"] = config.get("b-secondary-contributors-left", "")
        if config.get("b-secondary-contributors-right", "")!="":
            names.attrib["suffix"] = config.get("b-secondary-contributors-right", "")
        
        for name in namelist:
            name.attrib["and"] = config.get("b-and-form", "")
            name.attrib["delimiter"] = config.get("b-name-delimiter", "・")
            name.attrib["sort-separator"] = config.get("b-name-sort-separator", ",")
            name.attrib["delimiter-precedes-last"] = config.get("b-delimiter-precedes-last", "never")
            if config.get("b-name-initialize-with", "")!="":
                name.attrib["initialize-with"] = config.get("b-name-initialize-with", "")
                name.attrib["initialize"] = config.get("b-name-initialize", "")
                
            if config.get("b-secondary-contributor-name-as-sort-order", "")!="":
                name.attrib["name-as-sort-order"] = config.get("b-secondary-contributor-name-as-sort-order", "first")
            name.getparent().insert(0, name)
        
        for label in labels:
            label.attrib["prefix"] = config.get("b-contributor-2-label-left", " (")
            label.attrib["suffix"] = config.get("b-contributor-2-label-right", ")")
            label.attrib["form"] = "short"

        # contributors = self.macros.get("secondary-contributors", None)
        # labels = contributors.xpath("z:choose/z:if/z:group/z:names/z:label", namespaces=self.tools.ns)
        # for label in labels:
            # label.attrib["form"] = "short"
            # label.attrib["suffix"] = config.get("b-contributors-suffix", "、")
            # if config.get("b-invert-contributors-label", False):
                # label.getparent().insert(len(label.getparent().getchildren()), label)
            # else:
                # pass #Not move
                
        """
        Date
        """
        date = self.macros.get("date", None)
        group = date.xpath("z:choose/z:if/z:group", namespaces=self.tools.ns)[0]
        group.attrib["prefix"] = config.get("b-date-left", "（")
        group.attrib["suffix"] = config.get("b-date-right", "）")
        group.attrib["delimiter"] = config.get("b-date-delimiter", "")
        
        # Original date
        originaldate = group.xpath("z:date[@variable='original-date']", namespaces=self.tools.ns)[0]
        originaldate.attrib["prefix"] = config.get("c-original-date-left", "")
        originaldate.attrib["suffix"] = config.get("c-original-date-right", "=")
        originaldate.attrib.pop("form")
        originaldate.attrib.pop("date-parts")
        self.tools.appendchild(originaldate, "date-part", None, {"name": "year"})
        
        # No date
        nodate = date.xpath("z:choose/z:else/z:text", namespaces=self.tools.ns)[0]
        nodate.attrib["prefix"] =  config.get("b-date-left", "（")
        nodate.attrib["suffix"] =  config.get("b-date-right", "）")
        
        """
        Title
        """
        title = self.macros.get("title", None)
        t = title.xpath("z:choose/z:else/z:text", namespaces=self.tools.ns)[0]
        t.attrib["quotes"] = config.get("b-title-quotes", "true")
        
        """
        Book title
        """
        title = self.macros.get("title", None)
        booktitle = title.xpath("z:choose/z:else-if[@type='bill book graphic legislation motion_picture song']/z:text", namespaces=self.tools.ns)[0]
        if config.get("b-book-title-style", "")=="":
            booktitle.attrib.pop("font-style")
        else:
            booktitle.attrib["font-style"] = config.get("b-book-title-style")
            
        booktitle.attrib["prefix"] = config.get("b-book-title-left", "『")
        booktitle.attrib["suffix"] = config.get("b-book-title-right", "』")
        
        """
        Container title
        """
        title = self.macros.get("container-title", None)
        # website title
        websitetitle = title.xpath("z:choose/z:if[@type='webpage']/z:text", namespaces=self.tools.ns)[0]
        websitetitle.attrib["prefix"] = config.get("b-website-title-left", "")
        
        # book title
        containertitle = title.xpath("z:choose/z:else-if/z:group/z:text", namespaces=self.tools.ns)[0]
        if config.get("b-book-title-style", "")=="":
            containertitle.attrib.pop("font-style")
        else:
            containertitle.attrib["font-style"] = config.get("b-book-title-style")
        
        # if config.get("b-book-title-right", "") == config.get("b-journal-title-right", ""):
            # containertitle.attrib["prefix"] = config.get("b-book-title-left", "『")
            # containertitle.attrib["suffix"] = config.get("b-book-title-right", "』")
        # else:
        choose = self.tools.insertchild(0, containertitle.getparent(), "choose", None, {})
        book = self.tools.insertchild(0, choose, "if", None, {"type": "chapter"})
        journal = self.tools.insertchild(1, choose, "else-if", None, {"type": "article-journal"})
        other = self.tools.insertchild(2, choose, "else", None, {})
        
        booktitle = copy.deepcopy(containertitle)
        journaltitle = copy.deepcopy(containertitle)
        
        booktitle.attrib["prefix"] = config.get("b-book-title-left", "『")
        booktitle.attrib["suffix"] = config.get("b-book-title-right", "』")
        book.insert(0, booktitle)

        journaltitle.attrib["prefix"] = config.get("b-journal-title-left", "")
        journaltitle.attrib["suffix"] = config.get("b-journal-title-right", "")
        journal.insert(0, journaltitle)
        
        other.insert(0, containertitle)
        
        # Journal title suffix
        # t = title.xpath(
        
        # Change container-title prefix
        # title = self.bibliographylayout.xpath("z:text[@macro='container-title"+self.langsuffix+"']", namespaces=self.tools.ns)[0]
        # title.attrib["prefix"] = config.get("b-book-title-prefix", ". ")
        
        """
        Journal title (collection-title)
        """
        title = self.macros.get("collection-title", None).xpath("z:choose/z:if/z:choose/z:if/z:group", namespaces=self.tools.ns)[0]
        title.attrib["delimiter"] = config.get("b-journal-title-suffix", ",")
                
        
        """
        Edition
        """
        edition = self.bibliographylayout.xpath("z:text[@macro='edition"+self.langsuffix+"']", namespaces=self.tools.ns)[0]
        edition.attrib["suffix"] = config.get("b-edition-right", "")
        
        # Remove prefix
        editionnumeric = self.macros.get("edition", None).xpath("z:choose/z:if/z:choose/z:if/z:group", namespaces=self.tools.ns)[0]
        editiontext = self.macros.get("edition", None).xpath("z:choose/z:if/z:choose/z:else/z:text", namespaces=self.tools.ns)[0]
        editionnumeric.attrib.pop("prefix")
        editiontext.attrib.pop("prefix")
        
        
        """
        issue
        """
        issue = self.macros.get("issue", None).xpath("z:choose/z:else/z:group", namespaces=self.tools.ns)[0]
        issue.attrib.pop("prefix")
        issue.attrib["delimiter"] = config.get("b-issue-delimiter", "、")
        
        """
        Locators (volume and issue for article)
        """
        # Add punctuation after locator
        locators = self.bibliographylayout.xpath("z:text[@macro='locators"+self.langsuffix+"']", namespaces=self.tools.ns)[0]
        locators.attrib["suffix"] = config.get("b-locator-right", "")
        
        locators = self.macros.get("locators", None)
        
        #volume and issue present
        volume = locators.xpath("z:choose/z:if/z:choose/z:if", namespaces=self.tools.ns)[0]
        vtext = locators.xpath("z:choose/z:if/z:choose/z:if/z:text", namespaces=self.tools.ns)[0]
        group = locators.xpath("z:choose/z:if/z:choose/z:if/z:group", namespaces=self.tools.ns)[0]
            
        
        #add comma between volume and issue
        volumeissuegroup = SubElement(volume, "group")
        volume.insert(0, volumeissuegroup)
        
        issue = locators.xpath("z:choose/z:if/z:choose/z:if/z:group/z:choose/z:if", namespaces=self.tools.ns)[0]
        issued = locators.xpath("z:choose/z:if/z:choose/z:if/z:group/z:choose/z:else", namespaces=self.tools.ns)[0]
        
        if config.get("b-locator-label-form", "")!="":
            vgroup = SubElement(volume, "group")
            vlabel = SubElement(vgroup, "label")
            vgroup.insert(0, vtext)
            vgroup.attrib["delimiter"] = config.get("b-locator-label-delimiter", "")
            vlabel.attrib["variable"] = "volume"
            vlabel.attrib["form"] = "short"
            vlabel.attrib["text-case"] = "capitalize-first"
            volume.insert(0, vgroup)
                        
            itext = locators.xpath("z:choose/z:if/z:choose/z:if/z:group/z:choose/z:if/z:text", namespaces=self.tools.ns)[0]
            if config.get("b-locator-label-invert", False):
                vgroup.insert(1, vlabel)
                itext.attrib["prefix"] = config.get("b-issue-left", "")
                
                if config.get("b-volume-right", "")!="":
                    vlabel.attrib["suffix"] = config.get("b-volume-right", "")
 
                # label.attrib["suffix"] = config.get("b-issue-right", "")
                vtext.attrib["prefix"] = config.get("b-volume-left", "")
                if config.get("b-locator-label-form", "")!="":
                    ilabel = self.tools.appendchild(issue, "label", None, {"variable": "issue", "form": "short"})
                    if config.get("b-issue-right", "")!="":
                        ilabel.attrib["suffix"] = config.get("b-issue-right", "")
            else:
                vgroup.insert(0, vlabel)
                itext.attrib["suffix"] = config.get("b-issue-right", "")
                label.attrib["prefix"] = config.get("b-issue-left", "")
                if config.get("b-locator-label-form", "")!="":
                    ilabel  = self.tools.insertchild(0, issue, "label", None, {"variable": "issue", "form": "short", "text-case": "capitalize-first"})
            volumeissuegroup.insert(0, vgroup)
        else: # No label
            itext = issue.xpath("z:text", namespaces=self.tools.ns)[0]
            itext.attrib["prefix"] = config.get("b-issue-left", "")
            itext.attrib["suffix"] = config.get("b-issue-right", "")
            
            volif = locators.xpath("z:choose/z:if/z:choose/z:if", namespaces=self.tools.ns)[0]
            votext = locators.xpath("z:choose/z:if/z:choose/z:if/z:text", namespaces=self.tools.ns)[0]
            volif.insert(0, votext)
            
            
        # text.attrib.pop("prefix")
        group.attrib.pop("prefix") # = config.get("b-issue-left", "")
        group.attrib.pop("suffix") # = config.get("b-issue-right", "")
        group.attrib["delimiter"] = config.get("b-locator-label-delimiter", "")
        
        
        igroup = issued.getparent().getparent()
        volumeissuegroup.insert(1, igroup)
        
        # add delimiter
        volumeissuegroup.attrib["delimiter"] = config.get("b-volume-issue-delimiter", "")
        
        # Only issue present
        issue = locators.xpath("z:choose/z:if/z:choose/z:else-if/z:group/z:text[@variable='issue']", namespaces=self.tools.ns)[0]

        ilabel = locators.xpath("z:choose/z:if/z:choose/z:else-if/z:group/z:text[@term='issue']", namespaces=self.tools.ns)[0]
        group = locators.xpath("z:choose/z:if/z:choose/z:else-if/z:group", namespaces=self.tools.ns)[0]
        
        if config.get("b-locator-label-invert", False):
            ilabel.getparent().insert(len(ilabel.getparent().getchildren()), ilabel)
            issue.attrib["prefix"] = config.get("b-only-issue-left", "")
            ilabel.attrib["suffix"] = config.get("b-only-issue-right", "")
            ilabel.getparent().attrib["delimiter"] = config.get("b-locator-label-delimiter", "")
        else:
            ilabel.getparent().insert(0, ilabel)
            ilabel.attrib["text-case"] = "capitalize-first"
            ilabel.attrib["prefix"] = config.get("b-only-issue-left", "")
            ilabel.getparent().attrib["delimiter"] = config.get("b-locator-label-delimiter", "")
            issue.attrib["suffix"] = config.get("b-only-issue-right", "")
        
        group.attrib.pop("prefix")

        # Only issued present
        issued = locators.xpath("z:choose/z:if/z:choose/z:else", namespaces=self.tools.ns)[0]
        # self.tools.appendchild(issued, "label", None, {"variable": "issued", "form": "short"})
        
        """
        Locators chapter
        """
        locatorschapter = self.macros.get("locators-chapter", None)
        group = locatorschapter.xpath("z:choose/z:if/z:choose/z:if/z:group", namespaces=self.tools.ns)[0]
        group.attrib["prefix"] = config.get("b-locator-chapter-prefix", "、")
        locatorform = config.get("b-locator-chapter-label-form", "long")
        
        if  config.get("b-locator-chapter-label-invert", False):
            self.tools.appendchild(group, "label", None, {"form": locatorform, "variable": "page"})
        else:
            sep = config.get("b-locator-chapter-separator", False)
            self.tools.insertchild(0, group, "label", None, {"form": locatorform, "variable": "page", "suffix": sep})
            
        """
        Locators article
        """
        locatorsarticle = self.macros.get("locators-article", None)
        volpage = locatorsarticle.xpath("z:choose/z:else-if/z:choose/z:if/z:text", namespaces=self.tools.ns)[0]
        page = locatorsarticle.xpath("z:choose/z:else-if/z:choose/z:else/z:text", namespaces=self.tools.ns)[0]
        volpage.attrib["prefix"] = config.get("b-locator-article-prefix", "、") #need checking
        
        if config.get("b-article-page-label-invert", False):
            if config.get("b-locator-label-form", "")!="":
                self.tools.appendchild(volpage.getparent(), "label", None, {"form": config.get("b-locator-label-form", "long"), "variable": "page", "prefix":config.get("b-locator-label-delimiter", "")})
        else:
            if config.get("b-locator-label-form", "")!="":
                self.tools.insertchild(0, volpage.getparent(), "label", None, {"form": config.get("b-locator-label-form", "long"), "variable": "page", "suffix":config.get("b-locator-label-delimiter", "")})
        
        page.attrib["prefix"] = config.get("b-locator-article-prefix", "、") #need checking
        
        if config.get("b-article-page-label-invert", False):
            if config.get("b-locator-label-form", "")!="":
                self.tools.appendchild(page.getparent(), "label", None, {"form": config.get("b-locator-label-form", "long"), "variable": "page", "prefix":config.get("b-locator-label-delimiter", "")})
        else:
            if config.get("b-locator-label-form", "")!="":
                self.tools.insertchild(0, page.getparent(), "label", None, {"form": config.get("b-locator-label-form", "long"), "variable": "page", "suffix":config.get("b-locator-label-delimiter", "")})
            
        """
        Access
        """
        #remove prefix from access in layout
        a = self.bibliographylayout.xpath("z:text[@macro='access"+self.langsuffix+"']", namespaces=self.tools.ns)[0]
        if "prefix" in a.attrib:
            a.attrib.pop("prefix")
        
        access = self.macros.get("access", None)
        group = access.xpath("z:group", namespaces=self.tools.ns)[0]
        group.attrib.pop("delimiter")
        urldoi = access.xpath("z:group/z:choose/z:if[@type='legal_case']", namespaces=self.tools.ns)[0].getparent()
        urldoi.getparent().insert(0, urldoi)
        issuedgroup = access.xpath("z:group/z:choose/z:if[@type='webpage post-weblog']", namespaces=self.tools.ns)[0]
        
        accessed = access.xpath("z:group/z:choose/z:if[@variable='issued']/z:group", namespaces=self.tools.ns)[0]
        accessedlabel = access.xpath("z:group/z:choose/z:if[@variable='issued']/z:group/z:text", namespaces=self.tools.ns)[0]
        
        if not config.get("b-accessed-label-added", False):
            accessed.remove(accessedlabel)
        
        issuedgroup.insert(0, accessed)
        
        #remove issued date = force accessed date
        issued = access.xpath("z:group/z:choose/z:if[@type='webpage post-weblog']/z:date", namespaces=self.tools.ns)[0]
        issuedgroup.remove(issued)
        
        accessed.attrib["prefix"] = config.get("a-bracket-left", "（")
        accessed.attrib["suffix"] = config.get("a-bracket-right", "）")
        accessed.attrib["delimiter"] = config.get("b-accessed-label-right", "")