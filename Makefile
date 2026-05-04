PYTHON  := python3
SCRIPT  := csv_to_html.py
CSV     := PhDApplications.csv
HTML    := PhDApplications.html

.PHONY: all clean push

all: $(HTML)

# Rebuild the HTML whenever the CSV or the conversion script changes
$(HTML): $(CSV) $(SCRIPT)
	$(PYTHON) $(SCRIPT) $(CSV) $(HTML)

clean:
	rm -f $(HTML)

push: $(HTML)
	git add $(HTML)
	git diff --cached --quiet || git commit -m "Update application tracker"
	git push -u origin main
