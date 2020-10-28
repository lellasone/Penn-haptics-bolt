all: ROS_NOBUILD

#Check for 32 or 64 bit Kernel
#i686 if 32-bit
#x86_64 if 64-bit
# No "." in names for my website
CHEETAH_VERSION = v320

#name for file download purposes
TARBALL_NAME_D = cheetah-api-linux-x86_64-v320
TARBALL_NAME = cheetah-api-linux-x86_64-v3.20
TARBALL = build/$(TARBALL_NAME).zip
TARBALL_URL = http://jake-ketchum.squarespace.com/s/$(TARBALL_NAME_D).zip
SOURCE_DIR = build/$(TARBALL_NAME)
UNPACK_CMD = unzip
include $(shell rospack find mk)/download_unpack_build.mk

ROS_NOBUILD: $(SOURCE_DIR)/unpacked
	mkdir -p lib
	cp $(SOURCE_DIR)/c/cheetah.so lib
	touch ROS_NOBUILD
	echo "created by rosmake to mark as installed" >> ROS_NOBUILD


clean:
	-rm -f ROS_NOBUILD
	-rm -rf lib

wipe: clean
	-rm -rf build
