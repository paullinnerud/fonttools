from __future__ import print_function, division, absolute_import
from fontTools import ttLib
from fontTools.ttLib.tables import otTables as ot

# VariationStore

def buildVarRegionAxis(axisSupport):
	self = ot.VarRegionAxis()
	self.StartCoord, self.PeakCoord, self.EndCoord = [float(v) for v in axisSupport]
	return self

def buildVarRegion(support, axisTags):
	assert all(tag in axisTags for tag in support.keys()), ("Unknown axis tag found.", support, axisTags)
	self = ot.VarRegion()
	self.VarRegionAxis = []
	for tag in axisTags:
		self.VarRegionAxis.append(buildVarRegionAxis(support.get(tag, (0,0,0))))
	self.VarRegionAxisCount = len(self.VarRegionAxis)
	return self

def buildVarRegionList(supports, axisTags):
	self = ot.VarRegionList()
	self.RegionAxisCount = len(axisTags)
	self.Region = []
	for support in supports:
		self.Region.append(buildVarRegion(support, axisTags))
	self.RegionCount = len(self.Region)
	return self


def _reorderItem(lst, narrows, zeroes):
	out = []
	count = len(lst)
	for i in range(count):
		if i not in narrows:
			out.append(lst[i])
	for i in range(count):
		if i in narrows  and i not in zeroes:
			out.append(lst[i])
	return out

def VarData_CalculateNumShorts(self, optimize=True):
	count = self.VarRegionCount
	items = self.Item
	narrows = set(range(count))
	zeroes = set(range(count))
	for item in items:
		wides = [i for i in narrows if not (-128 <= item[i] <= 127)]
		narrows.difference_update(wides)
		nonzeroes = [i for i in zeroes if item[i]]
		zeroes.difference_update(nonzeroes)
		if not narrows and not zeroes:
			break
	if optimize:
		# Reorder columns such that all SHORT columns come before UINT8
		self.VarRegionIndex = _reorderItem(self.VarRegionIndex, narrows, zeroes)
		self.VarRegionCount = len(self.VarRegionIndex)
		for i in range(self.ItemCount):
			items[i] = _reorderItem(items[i], narrows, zeroes)
		self.NumShorts = count - len(narrows)
	else:
		wides = set(range(count)) - narrows
		self.NumShorts = 1+max(wides) if wides else 0
	return self

def buildVarData(varRegionIndices, items, optimize=True):
	self = ot.VarData()
	self.VarRegionIndex = list(varRegionIndices)
	regionCount = self.VarRegionCount = len(self.VarRegionIndex)
	records = self.Item = []
	if items:
		for item in items:
			assert len(item) == regionCount
			records.append(list(item))
	self.ItemCount = len(self.Item)
	VarData_CalculateNumShorts(self, optimize=optimize)
	return self


def buildVarStore(varRegionList, varDataList):
	self = ot.VarStore()
	self.Format = 1
	self.VarRegionList = varRegionList
	self.VarData = list(varDataList)
	self.VarDataCount = len(self.VarData)
	return self


# Variation helpers

def buildVarIdxMap(varIdxes, glyphOrder):
	self = ot.VarIdxMap()
	self.mapping = {g:v for g,v in zip(glyphOrder, varIdxes)}
	return self

def buildVarDevTable(varIdx):
	self = ot.Device()
	self.DeltaFormat = 0x8000
	self.StartSize = varIdx >> 16
	self.EndSize = varIdx & 0xFFFF
	return self
