PATH=/usr/share/texmf/bin:/bin:/usr/bin:/usr/local/bin:/usr/X11R6/bin
PROG_PATH=/usr/share/texmf/bin

.SUFFIXES:
.SUFFIXES: .fig .eps .pdf .ps

#.fig.eps:; /usr/X11R6/bin/fig2dev -L eps $*.fig > $@
#.eps.pdf:; epstopdf $*.eps

FIGS=rack1/dell2950-12interface.pdf  \
rack1/dell2950-6interface.pdf \
rack1/powerswitch14.pdf \
rack1/powerswitch7.pdf \
rack1/rack1.pdf \
rack1/serial7.pdf \
rack1/switch16.pdf \
rack1/powerswitch4.pdf \
rack2/dell1950.pdf \
rack2/powerswitch5.pdf \
rack2/powerswitch8.pdf \
rack2/rack2.pdf \
rack2/serial2.pdf \
rack2/switch11.pdf \
rack2/switch15.pdf \
rack3/x4100.pdf \
rack3/switch7.pdf \
rack3/powerswitch10.pdf \
rack3/powerswitch9.pdf \
rack3/rack3.pdf \
rack3/serial4.pdf \
rack3/switch10.pdf \
rack3/switch12.pdf \
rack4/force10.pdf \
rack4/dell2950-3interface.pdf \
rack4/rack4.pdf \
rack4/switch17.pdf \
rack4/powerswitch13.pdf \
rack5/dell1850.pdf \
rack5/delloptiplex.pdf \
rack5/powerswitch6.pdf \
rack5/rack5.pdf \
rack5/serial5.pdf \
rack5/sunv20z.pdf \
rack5/switch10.pdf \
rack5/switch1.pdf \
rack6/arkell.pdf \
rack6/cockerel.pdf \
rack6/powerswitch3.pdf \
rack6/rack6.pdf \
rack6/serial3.pdf \
rack6/switch3.pdf \
rack6/switch4.pdf \
rack6/switch5.pdf \
rack6/temp-switch5.pdf \
underfloor/underfloor.pdf 


all: $(FIGS) pdf ps

ps : wiring.pdf
	pdftops wiring.pdf wiring.ps
pdf: $(FIGS) wiring.tex
	pdflatex wiring.tex
	pdflatex wiring.tex

%.pdf : %.fig
	fig2dev -L pdf $< > $@
clean:
	/bin/rm -f *dvi *log *aux *blg *bbl *toc *ps *pdf *~ $(FIGS)
tidy:
	/bin/rm -f *dvi *log *aux *blg *bbl *toc 


