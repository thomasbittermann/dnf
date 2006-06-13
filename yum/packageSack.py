#!/usr/bin/python -tt
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
# Copyright 2006 Duke University

from Errors import PackageSackError
import rpmUtils.miscutils

class PackageSackBase:
    """Base class that provides the interface for PackageSacks."""
    def __init__(self):
        self.added = {}

    def __len__(self):
        return len(self.simplePkgList())
        
    def __iter__(self):
        if hasattr(self.returnPackages(), '__iter__'):
            return self.returnPackages().__iter__()
        else:
            return iter(self.returnPackages())

    def setCompatArchs(self, compatArchs):
        raise NotImplementedError()

    def populate(self, repo, with, callback, cacheOnly):
        raise NotImplementedError()
        
    def packagesByTuple(self, pkgtup):
        """return a list of package objects by (n,a,e,v,r) tuple"""
        raise NotImplementedError()
        
    def searchNevra(self, name=None, epoch=None, ver=None, rel=None, arch=None):
        """return list of pkgobjects matching the nevra requested"""
        raise NotImplementedError()
           
    def searchRequires(self, name):
        """return list of package requiring the name (any evr and flag)"""
        raise NotImplementedError()

    def searchProvides(self, name):
        """return list of package providing the name (any evr and flag)"""
        raise NotImplementedError()

    def searchConflicts(self, name):
        """return list of package conflicting with the name (any evr and flag)"""
        raise NotImplementedError()

    def searchObsoletes(self, name):
        """return list of package obsoleting the name (any evr and flag)"""
        raise NotImplementedError()

    def returnObsoletes(self):
        """returns a dict of obsoletes dict[obsoleting pkgtuple] = [list of obs]"""
        raise NotImplementedError()

    def searchFiles(self, file):
        """return list of packages by filename"""
        raise NotImplementedError()

    def addPackage(self, obj):
        """add a pkgobject to the packageSack"""
        raise NotImplementedError()

    def buildIndexes(self):
        """builds the useful indexes for searching/querying the packageSack
           This should be called after all the necessary packages have been
           added/deleted"""
        raise NotImplementedError()

    def delPackage(self, obj):
        """delete a pkgobject"""
        raise NotImplementedError()

    def returnPackages(self):
        """return list of all packages"""
        raise NotImplementedError()

    def returnNewestByNameArch(self, naTup=None):
        """return list of newest packages based on name, arch matching
           this means(in name.arch form): foo.i386 and foo.noarch are not
           compared to each other for highest version only foo.i386 and
           foo.i386 will be compared"""
        raise NotImplementedError()

    def returnNewestByName(self, name=None):
        """return list of newest packages based on name matching
           this means(in name.arch form): foo.i386 and foo.noarch will
           be compared to each other for highest version"""
        raise NotImplementedError()

    def simplePkgList(self):
        """returns a list of pkg tuples (n, a, e, v, r)"""
        raise NotImplementedError()

    def printPackages(self):
        raise NotImplementedError()

    def excludeArchs(self, archlist):
        """exclude incompatible arches. archlist is a list of compatible arches"""
        raise NotImplementedError()

    def searchPackages(self, fields, criteria_re, callback):
        raise NotImplementedError()


class MetaSack(PackageSackBase):
    """Represents the aggregate of multiple package sacks, such that they can
       all be treated as one unified sack."""

    def __init__(self):
        PackageSackBase.__init__(self)
        self.sacks = {}
        self.compatarchs = None

    def addSack(self, repoid, sack):
        """Adds a repository's packageSack to this MetaSack."""
        self.sacks[repoid] = sack

        # Make sure the new sack follows the same rules we have been given.
        sack.setCompatArchs(self.compatarchs)

    def populate(self, repo, with, callback, cacheOnly):
        self.sacks[repo.id].populate(repo, with, callback, cacheOnly)

    def setCompatArchs(self, compatArchs):
        for sack in self.sacks.values():
            sack.setCompatArchs(compatArchs)

    def packagesByTuple(self, pkgtup):
        """return a list of package objects by (n,a,e,v,r) tuple"""
        return self._computeAggregateListResult("packagesByTuple", pkgtup)

    def searchNevra(self, name=None, epoch=None, ver=None, rel=None, arch=None):
        """return list of pkgobjects matching the nevra requested"""
        return self._computeAggregateListResult("searchNevra", name, epoch, ver, rel, arch)

    def searchRequires(self, name):
        """return list of package requiring the name (any evr and flag)"""
        return self._computeAggregateListResult("searchRequires", name)

    def searchProvides(self, name):
        """return list of package providing the name (any evr and flag)"""
        return self._computeAggregateListResult("searchProvides", name)

    def searchConflicts(self, name):
        """return list of package conflicting with the name (any evr and flag)"""
        return self._computeAggregateListResult("searchConflicts", name)

    def searchObsoletes(self, name):
        """return list of package obsoleting the name (any evr and flag)"""
        return self._computeAggregateListResult("searchObsoletes", name)

    def returnObsoletes(self):
        """returns a dict of obsoletes dict[obsoleting pkgtuple] = [list of obs]"""
        return self._computeAggregateDictResult("returnObsoletes")

    def searchFiles(self, file):
        """return list of packages by filename"""
        return self._computeAggregateListResult("searchFiles", file)

    def addPackage(self, obj):
        """Add a pkgobject to the packageSack.  This is a meaningless operation
           for the MetaSack."""
        pass

    def buildIndexes(self):
        """builds the useful indexes for searching/querying the packageSack
           This should be called after all the necessary packages have been
           added/deleted"""
        for sack in self.sacks.values():
            sack.buildIndexes()

    def delPackage(self, obj):
        """Delete a pkgobject if it exists in every sub-sack."""
        sack = self.sacks[obj.repoid]
        sack.delPackage(obj)


    def returnPackages(self, repoid=None):
        """return list of all packages, takes optional repoid"""
        if not repoid:
            return self._computeAggregateListResult("returnPackages")
        return self.sacks[repoid].returnPackages()

    def returnNewestByNameArch(self, naTup=None):
        """return list of newest packages based on name, arch matching
           this means(in name.arch form): foo.i386 and foo.noarch are not
           compared to each other for highest version only foo.i386 and
           foo.i386 will be compared"""
        return self._computeAggregateListResult("returnNewestByNameArch", naTup)

    def returnNewestByName(self, name=None):
        """return list of newest packages based on name matching
           this means(in name.arch form): foo.i386 and foo.noarch will
           be compared to each other for highest version"""
        return self._computeAggregateListResult("returnNewestByName", name)

    def simplePkgList(self, repoid=None):
        """returns a list of pkg tuples (n, a, e, v, r) optionally from a
           single repoid"""
        if not repoid:
            return self._computeAggregateListResult("simplePkgList")
        return self.sacks[repoid].simplePkgList()

    def printPackages(self):
        for sack in self.sacks.values():
            sack.printPackages()

    def excludeArchs(self, archlist):
        """exclude incompatible arches. archlist is a list of compatible arches"""
        for sack in self.sacks.values():
            sack.excludeArchs(archlist)

    def searchPackages(self, fields, criteria_re, callback):
        return self._computeAggregateDictResult("searchPackages", fields, criteria_re, callback)

    def _computeAggregateListResult(self, methodName, *args):
        result = []
        for sack in self.sacks.values():
            if hasattr(sack, methodName):
                method = getattr(sack, methodName)
                sackResult = apply(method, args)
                if sackResult:
                    result.extend(sackResult)
        return result

    def _computeAggregateDictResult(self, methodName, *args):
        result = {}
        for sack in self.sacks.values():
            if hasattr(sack, methodName):
                method = getattr(sack, methodName)
                sackResult = apply(method, args)
                if sackResult:
                    result.update(sackResult)
        return result



class PackageSack(PackageSackBase):
    """represents sets (sacks) of Package Objects"""
    def __init__(self):
        self.nevra = {} #nevra[(Name, Epoch, Version, Release, Arch)] = []
        self.obsoletes = {} #obs[obsoletename] = [pkg1, pkg2, pkg3] 
                 #the package lists are packages that obsolete the key name
        self.requires = {} #req[reqname] = [pkg1, pkg2, pkg3]
                 #the package lists are packages that require the key name
        self.provides = {} #ditto of above but for provides
        self.conflicts = {} #ditto of above but for conflicts
        self.filenames = {} # duh
        self.pkgsByRepo = {} #pkgsByRepo['repoid']= [pkg1, pkg2, pkg3]
        self.pkgsByID = {} #pkgsById[pkgid] = [pkg1, pkg2] (should really only ever be one value but
                           #you might have repos with the same package in them
        self.compatarchs = None # dict of compatible archs for addPackage
        self.indexesBuilt = 0
        
        
    def __len__(self):
        return len(self.simplePkgList())
    
    def __iter__(self):
        if hasattr(self.returnPackages(), '__iter__'):
            return self.returnPackages().__iter__()
        else:
            return iter(self.returnPackages())

    def _checkIndexes(self, failure='error'):
        """check to see if the indexes are built, if not do what failure demands
           either error out or build the indexes, default is to error out"""
           
        if not self.indexesBuilt:
            if failure == 'error':
                raise PackageSackError, 'Indexes not yet built, cannot search'
            elif failure == 'build':
                self.buildIndexes()

    def setCompatArchs(self, compatarchs):
        self.compatarchs = compatarchs

    def packagesByTuple(self, pkgtup):
        """return a list of package objects by (n,a,e,v,r) tuple"""
        (n,a,e,v,r) = pkgtup
        return self.searchNevra(name=n, arch=a, epoch=e, ver=v, rel=r)
        
    def searchNevra(self, name=None, epoch=None, ver=None, rel=None, arch=None):
        """return list of pkgobjects matching the nevra requested"""
        self._checkIndexes(failure='build')
        if self.nevra.has_key((name, epoch, ver, rel, arch)):
            return self.nevra[(name, epoch, ver, rel, arch)]
        else:
            return []
           
    def searchRequires(self, name):
        """return list of package requiring the name (any evr and flag)"""
        self._checkIndexes(failure='build')        
        if self.requires.has_key(name):
            return self.requires[name]
        else:
            return []

    def searchProvides(self, name):
        """return list of package providing the name (any evr and flag)"""
        # FIXME - should this do a pkgobj.checkPrco((name, flag, (e,v,r,))??
        # has to do a searchFiles and a searchProvides for things starting with /
        self._checkIndexes(failure='build')        
        returnList = []
        if name[0] == '/':
             returnList.extend(self.searchFiles(name))
        if self.provides.has_key(name):
            returnList.extend(self.provides[name])
        return returnList

    def searchConflicts(self, name):
        """return list of package conflicting with the name (any evr and flag)"""
        self._checkIndexes(failure='build')        
        if self.conflicts.has_key(name):
            return self.conflicts[name]
        else:
            return []

    def searchObsoletes(self, name):
        """return list of package obsoleting the name (any evr and flag)"""
        self._checkIndexes(failure='build')        
        if self.obsoletes.has_key(name):
            return self.obsoletes[name]
        else:
            return []

    def returnObsoletes(self):
        """returns a dict of obsoletes dict[obsoleting pkgtuple] = [list of obs]"""
        obs = {}
        for po in self.returnPackages():
            pkgtuple = po.returnPackageTuple()
            if len(po.returnPrco('obsoletes')) == 0:
                continue

            if not obs.has_key(pkgtuple):
                obs[pkgtuple] = po.returnPrco('obsoletes')
            else:
                obs[pkgtuple].extend(po.returnPrco('obsoletes'))
        
        return obs
        
    def searchFiles(self, file):
        """return list of packages by filename
           FIXME - need to add regex match against keys in file list
        """
        self._checkIndexes(failure='build')
        if self.filenames.has_key(file):
            return self.filenames[file]
        else:
            return []

    def _addToDictAsList(self, dict, key, data):
        if not dict.has_key(key):
            dict[key] = []
        #if data not in dict[key]: - if I enable this the whole world grinds to a halt
        # need a faster way of looking for the object in any particular list
        dict[key].append(data)

    def _delFromListOfDict(self, dict, key, data):
        if not dict.has_key(key):
            dict[key] = []
        try:
            dict[key].remove(data)
        except ValueError:
            pass
            
        if len(dict[key]) == 0: # if it's an empty list of the dict, then kill it
            del dict[key]
            
            
    def addPackage(self, obj):
        """add a pkgobject to the packageSack"""

        repoid = obj.returnSimple('repoid')
        (name, epoch, ver, rel, arch) = obj.returnNevraTuple()
        
        if self.compatarchs:
            if self.compatarchs.has_key(arch):
                self._addToDictAsList(self.pkgsByRepo, repoid, obj)
        else:
            self._addToDictAsList(self.pkgsByRepo, repoid, obj)


    def buildIndexes(self):
        """builds the useful indexes for searching/querying the packageSack
           This should be called after all the necessary packages have been 
           added/deleted"""
        
        # blank out the indexes
        self.obsoletes = {}
        self.requires = {}
        self.provides = {}
        self.conflicts = {}
        self.filenames = {}
        self.nevra = {}
        self.pkgsByID = {}
        
        for repoid in self.pkgsByRepo.keys():
            for obj in self.pkgsByRepo[repoid]:
            # store the things provided just on name, not the whole require+version
            # this lets us reduce the set of pkgs to search when we're trying to depSolve
                for (n, fl, (e,v,r)) in obj.returnPrco('obsoletes'):
                    self._addToDictAsList(self.obsoletes, n, obj)
                for (n, fl, (e,v,r)) in obj.returnPrco('requires'):
                    self._addToDictAsList(self.requires, n, obj)
                for (n, fl, (e,v,r)) in obj.returnPrco('provides'):
                    self._addToDictAsList(self.provides, n, obj)
                for (n, fl, (e,v,r)) in obj.returnPrco('conflicts'):
                    self._addToDictAsList(self.conflicts, n, obj)
                for ftype in obj.returnFileTypes():
                    for file in obj.returnFileEntries(ftype):
                        self._addToDictAsList(self.filenames, file, obj)
                self._addToDictAsList(self.pkgsByID, obj.returnSimple('id'), obj)
                (name, epoch, ver, rel, arch) = obj.returnNevraTuple()
                self._addToDictAsList(self.nevra, (name, epoch, ver, rel, arch), obj)
                self._addToDictAsList(self.nevra, (name, None, None, None, None), obj)
        
        self.indexesBuilt = 1
        

        
    def delPackage(self, obj):
        """delete a pkgobject"""
        self._delFromListOfDict(self.pkgsByRepo, obj.returnSimple('repoid'), obj)
        if self.indexesBuilt: # if we've built indexes, delete it b/c we've just deleted something
            self.indexesBuilt = 0
        
    def returnPackages(self, repoid=None):
        """return list of all packages, takes optional repoid"""
        returnList = []
        if repoid is None:
            for repo in self.pkgsByRepo.keys():
                returnList.extend(self.pkgsByRepo[repo])
        else:
            try:
                returnList = self.pkgsByRepo[repoid]
            except KeyError:
                # nothing to return
                pass
        
        return returnList

    def returnNewestByNameArch(self, naTup=None):
        """return list of newest packages based on name, arch matching
           this means(in name.arch form): foo.i386 and foo.noarch are not 
           compared to each other for highest version only foo.i386 and 
           foo.i386 will be compared"""
        highdict = {}
        # If naTup is set, only iterate through packages that match that
        # name
        if (naTup):
            where = self.nevra.get((naTup[0],None,None,None,None))
            if (not where):
                raise PackageSackError, 'No Package Matching %s.%s' % naTup
        else:
            where = self.returnPackages()

        for pkg in where:
            (n, e, v ,r, a) = pkg.returnNevraTuple()
            if not highdict.has_key((n, a)):
                highdict[(n, a)] = pkg
            else:
                pkg2 = highdict[(n, a)]
                (e2, v2, r2) = pkg2.returnEVR()
                rc = rpmUtils.miscutils.compareEVR((e,v,r), (e2, v2, r2))
                if rc > 0:
                    highdict[(n, a)] = pkg
        
        if naTup:
            if highdict.has_key(naTup):
                return highdict[naTup]
            else:
                raise PackageSackError, 'No Package Matching %s.%s' % naTup
        
        return highdict.values()
        
    def returnNewestByName(self, name=None):
        """return list of newest packages based on name matching
           this means(in name.arch form): foo.i386 and foo.noarch will
           be compared to each other for highest version"""
        highdict = {}
        for pkg in self.returnPackages():
            (n, e, v ,r, a) = pkg.returnNevraTuple()
            if not highdict.has_key(n):
                highdict[n] = []
                highdict[n].append(pkg)
            else:
                pkg2 = highdict[n][0]
                (e2, v2, r2) = pkg2.returnEVR()
                rc = rpmUtils.miscutils.compareEVR((e,v,r), (e2, v2, r2))
                if rc > 0:
                    highdict[n] = [pkg]
                elif rc == 0:
                    highdict[n].append(pkg)
                
        if name:
            if highdict.has_key(name):
                return highdict[name]
            else:
                raise PackageSackError, 'No Package Matching  %s' % name
                
        return highdict.values()
           
    def simplePkgList(self, repoid=None):
        """returns a list of pkg tuples (n, a, e, v, r) optionally from a single repoid"""
        simplelist = []
        for pkg in self.returnPackages(repoid):
            simplelist.append(pkg.returnPackageTuple())
        return simplelist
                       
    def printPackages(self):
        for pkg in self.returnPackages():
            print pkg.returnNevraPrintable()

    def excludeArchs(self, archlist):
        """exclude incompatible arches. archlist is a list of compatible arches"""
        
        for pkg in self.returnPackages():
            if pkg.arch not in archlist:
                self.delPackage(pkg)

    def searchPackages(self, fields, criteria_re, callback):
        matches = {}

        for po in self.returnPackages():
            tmpvalues = []
            for field in fields:
                value = po.returnSimple(field)
                if value and criteria_re.search(value):
                    tmpvalues.append(value)
            if len(tmpvalues) > 0:
                if callback:
                    callback(po, tmpvalues)
                matches[po] = tmpvalues
 
        return matches

class ListPackageSack(PackageSack):
    """Derived class from PackageSack to build new Sack from list of
       pkgObjects - like one returned from self.returnNewestByNameArch()
       or self.returnNewestByName()"""
       
    def __init__(self, Objlist=None):
        PackageSack.__init__(self)
        if Objlist is not None:
            self.addList(Objlist)
    
    def addList(self, ObjList):
        for pkgobj in ObjList:
            self.addPackage(pkgobj)
    
