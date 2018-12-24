all:
	chmod a+x JackAnalyzer
tar:
	-cvf ex10.tar JackTokenizer.py TokenTypes.py CompilationEngine.py JackAnalyzer.py JackAnalyzer Makefile