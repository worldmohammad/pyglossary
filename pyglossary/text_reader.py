from pyglossary.file_utils import fileCountLines
from pyglossary.entry_base import BaseEntry
from pyglossary.entry import Entry

from pyglossary.glossary_type import GlossaryType

from os.path import isfile
from typing import (
	Tuple,
	Iterator,
)

import logging
log = logging.getLogger("root")


class TextGlossaryReader(object):
	def __init__(self, glos: GlossaryType, hasInfo: bool = True):
		self._glos = glos
		self._filename = ""
		self._encoding = None
		self._file = None
		self._hasInfo = hasInfo
		self._leadingLinesCount = 0
		self._pendingEntries = []
		self._wordCount = None
		self._pos = -1
		self._fileCount = 1
		self._fileIndex = 0

	def open(self, filename: str, encoding: str = "utf-8") -> None:
		self._filename = filename
		self._encoding = encoding
		self._file = open(filename, "r", encoding=encoding)
		if self._hasInfo:
			self.loadInfo()

	def openNextFile(self) -> bool:
		self.close()
		nextFilename = f"{self._filename}.{self._fileIndex + 1}"
		if not isfile(nextFilename):
			# TODO: detect compressed file, like file.txt.1.gz
			log.warn(f"WARNING: next file not found: {nextFilename}")
			return False
		self._fileIndex += 1
		log.info(f"Reading next file: {nextFilename}")
		self._file = open(nextFilename, "r", encoding=self._encoding)
		if self._hasInfo:
			self.loadInfo()
		return True

	def close(self) -> None:
		if not self._file:
			return
		try:
			self._file.close()
		except Exception:
			log.exception(f"error while closing file {self._filename!r}")
		self._file = None

	def loadInfo(self) -> None:
		self._pendingEntries = []
		self._leadingLinesCount = 0
		try:
			while True:
				wordDefi = self.nextPair()
				if not wordDefi:
					continue
				word, defi = wordDefi
				if not self.isInfoWords(word):
					self._pendingEntries.append(Entry(word, defi))
					break
				self._leadingLinesCount += 1
				if isinstance(word, list):
					word = [self.fixInfoWord(w) for w in word]
				else:
					word = self.fixInfoWord(word)
				if not word:
					continue
				if not defi:
					continue
				self._glos.setInfo(word, defi)
		except StopIteration:
			pass

		if self._fileIndex == 0:
			fileCountStr = self._glos.getInfo("file_count")
			if fileCountStr:
				self._fileCount = int(fileCountStr)
				self._glos.setInfo("file_count", "")

	def __next__(self) -> BaseEntry:
		self._pos += 1
		try:
			return self._pendingEntries.pop(0)
		except IndexError:
			pass
		###
		try:
			wordDefi = self.nextPair()
		except StopIteration as e:
			if self._fileIndex < self._fileCount + 1:
				if self.openNextFile():
					return self.__next__()
			self._wordCount = self._pos
			raise e
		if not wordDefi:
			return
		word, defi = wordDefi
		###
		return Entry(word, defi)

	def __len__(self) -> int:
		if self._wordCount is None:
			log.debug("Try not to use len(reader) as it takes extra time")
			self._wordCount = fileCountLines(self._filename) - \
				self._leadingLinesCount
		return self._wordCount

	def __iter__(self) -> Iterator[BaseEntry]:
		return self

	def isInfoWord(self, word: str) -> bool:
		raise NotImplementedError

	def isInfoWords(self, arg: "Union[str, List[str]]") -> bool:
		if isinstance(arg, str):
			return self.isInfoWord(arg)
		if isinstance(arg, list):
			return self.isInfoWord(arg[0])
		raise TypeError(f"bad argument {arg}")

	def fixInfoWord(self, word: str) -> bool:
		raise NotImplementedError

	def nextPair(self) -> Tuple[str, str]:
		raise NotImplementedError
