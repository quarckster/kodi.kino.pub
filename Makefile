VERSION ?=
VIDEO_ADDON_STEM := video.kino.pub-"$(VERSION)"
VIDEON_ADDON_OUTPUTDIR := "$(VIDEO_ADDON_STEM)"
VIDEO_ADDON_ARCHIVE := "$(VIDEO_ADDON_STEM)".zip

REPO_ADDON_STEM := repo.kino.pub
REPO_ADDON_OUTPUTDIR := "$(REPO_ADDON_STEM)"
REPO_ADDON_ARCHIVE := "$(REPO_ADDON_STEM)".zip

video_addon:
	@test -n "$(VERSION)" || (echo "Missing VERSION variable" && exit 1)
	@echo "Creating video.kino.pub add-on archive"
	@echo "======================================"
	@mkdir "$(VIDEON_ADDON_OUTPUTDIR)"
	@VERSION="$(VERSION)" envsubst < src/addon.xml > "$(VIDEON_ADDON_OUTPUTDIR)"/addon.xml
	@rsync -rv --exclude=*.pyc --exclude=__pycache__/ src/resources src/addon.py LICENSE "$(VIDEON_ADDON_OUTPUTDIR)"
	@zip -rv -9 -m "$(VIDEO_ADDON_ARCHIVE)" "$(VIDEON_ADDON_OUTPUTDIR)"
	@echo

repo_addon:
	@echo "Creating repo.kino.pub add-on archive"
	@echo "====================================="
	@mkdir $(REPO_ADDON_OUTPUTDIR)
	@cp repo_src/addon.xml repo_src/icon.png "$(REPO_ADDON_OUTPUTDIR)"/
	@zip -rv -9 -m "$(REPO_ADDON_ARCHIVE)" $(REPO_ADDON_STEM)
	@echo

repo: video_addon repo_addon
	@test -n "$(VERSION)" || (echo "Missing VERSION variable" && exit 1)
	@echo "Creating repository add-on directory structure"
	@echo "=============================================="
	@mkdir -p repo/video.kino.pub
	@VERSION="$(VERSION)" envsubst < repo_src/addons.xml > repo/addons.xml
	@md5sum repo/addons.xml | cut -d " " -f 1 > repo/addons.xml.md5
	@mv "$(REPO_ADDON_ARCHIVE)" repo/
	@mv "$(VIDEO_ADDON_ARCHIVE)" repo/video.kino.pub/
	@echo

deploy: repo
	@test -n "$(NETLIFY_AUTH_TOKEN)" || (echo "Missing NETLIFY_AUTH_TOKEN variable" && exit 1)
	@test -n "$(NETLIFY_SITE_ID)" || (echo "Missing NETLIFY_SITE_ID variable" && exit 1)
	@echo "Deploying files to Netlify"
	@echo "=========================="
	podman run -t -e NETLIFY_AUTH_TOKEN -e NETLIFY_SITE_ID -v $(PWD):/mnt -w /mnt quay.io/quarck/netlify netlify deploy --dir=repo/ --prod

test_integration:
	pytest -v -k "(not test_unit)"

test_unit:
	pytest -v tests/test_unit.py

clean:
	rm -rf video.kino.pub-*.zip repo.kino.pub.zip repo/
