// $Id: raw_listen.c, v 1.5 2004 / 03 / 12 22: 05:54 idgay Exp $

/*
 * tab:4 "Copyright (c) 2000-2003 The Regents of the University  of
 * California.  All rights reserved.
 *
 * Permission to use, copy, modify, and distribute this software and its
 * documentation for any purpose, without fee, and without written agreement
 * is hereby granted, provided that the above copyright notice, the following
 * two paragraphs and the author appear in all copies of this software.
 *
 * IN NO EVENT SHALL THE UNIVERSITY OF CALIFORNIA BE LIABLE TO ANY PARTY FOR
 * DIRECT, INDIRECT, SPECIAL, INCIDENTAL, OR CONSEQUENTIAL DAMAGES ARISING
 * OUT OF THE USE OF THIS SOFTWARE AND ITS DOCUMENTATION, EVEN IF THE
 * UNIVERSITY OF CALIFORNIA HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH
 * DAMAGE.
 *
 * THE UNIVERSITY OF CALIFORNIA SPECIFICALLY DISCLAIMS ANY WARRANTIES,
 * INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY
 * AND FITNESS FOR A PARTICULAR PURPOSE.  THE SOFTWARE PROVIDED HEREUNDER IS
 * ON AN "AS IS" BASIS, AND THE UNIVERSITY OF CALIFORNIA HAS NO OBLIGATION TO
 * PROVIDE MAINTENANCE, SUPPORT, UPDATES, ENHANCEMENTS, OR MODIFICATIONS."
 *
 * Copyright (c) 2002-2003 Intel Corporation All rights reserved.
 *
 * This file is distributed under the terms in the attached INTEL-LICENSE
 * file. If you do not find these files, copies can be found by writing to
 * Intel Research Berkeley, 2150 Shattuck Avenue, Suite 1300, Berkeley, CA,
 * 94704.  Attention:  Intel License Inquiry.
 */

/*
 * read debug packets from tmote sky motes over serial
 * and print to stdout
 *
 * cobbled together from raw_listen.c from tinyos-1.x tools folder
 * and the original python script to do the same thing by Darren Bishop
 *
 * this mess by Alan Medlar
 */

#include <sys/types.h>
#include <sys/time.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <termios.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <stdlib.h>
#include <signal.h>
#ifdef __CYGWIN__
#include <windows.h>  // i don't have a winbox to test this on :-(
#endif

#define BAUDRATE B57600
//
#define SERIAL_DEVICE "/dev/hen/motes/USB0"

#define SYNC_BYTE 0x7e
#define ESCAPE_BYTE 0x7d
#define HEADER_LENGTH 10
#define TOSH_DATA_LENGTH 116

int             input_stream,
		output_stream;

void 		handle_sigterm(int sig);
void            usage(char *name);
int             open_input(const char *serial, unsigned long baud);

int
main(int argc, char **argv)
{
	unsigned char   c;
	int             cnt, insync = 0, count = 0, escaped = 0;
	char            packet[HEADER_LENGTH + TOSH_DATA_LENGTH + 2];
	fd_set          fds;
	char *s;

	if (argc != 3) {
		usage(argv[0]);
		exit(2);
	}

	input_stream = open_input(argv[1], B57600);
	output_stream = open(argv[2], O_RDWR | O_APPEND | O_CREAT, \
			S_IRUSR | S_IWUSR | S_IRGRP | S_IROTH ); // i don't remember having to do this before...
	if(output_stream == -1) {
		fprintf(stderr, "error opening %s\n", argv[2]);
		perror("");
		exit(1);
	}

	signal(SIGTERM, handle_sigterm);

//	s = "yoyo\n";

//	write(output_stream, s, strlen(s));
//	exit(0);

	while (1) {
		FD_ZERO(&fds);
		FD_SET(input_stream, &fds);
		cnt = select(input_stream + 1, &fds, NULL, NULL, NULL);

		if (cnt < 0) {
			fprintf(stderr, "select returned %i\n", cnt);
			continue;
		}
		cnt = read(input_stream, &c, 1);

		if (cnt < 0) {
			perror("error reading from serial port");
			exit(2);
		}
		if (cnt == 1) {
			//each packet has a SYNC_BYTE at the beginning and end
			if (c == SYNC_BYTE) {
				//start of frame
				if (insync == 0) {
					insync = 1;
					count = 0;
					continue;
				}
				if (count < HEADER_LENGTH) {
					//empty packet
					insync = escaped = count = 0;
					continue;
				}
				//end of frame
				// print packet contents, reset vars
				packet[count - 2] = '\n';
				packet[count - 1] = '\0';
				//printf("%s\n", &packet[HEADER_LENGTH + 1]);
				//fflush(stdout);
				s = &packet[HEADER_LENGTH + 1];
				write(output_stream, s, strlen(s));
				insync = escaped = count = 0;
			}
			if (insync == 0) {
				continue;
			}
			if (c == ESCAPE_BYTE && !escaped) {
				escaped = 1;
				continue;
			}
			if (escaped) {
				escaped = 0;
				if (c == SYNC_BYTE || c == ESCAPE_BYTE) {
					insync = 0;
					continue;
				}
				c = c ^ 0x20;
			}
			packet[count++] = c;
		}
	}
}

void usage(char *name)
{
	fprintf(stderr, "usage: %s <serial port> <output file>\n", name);
}

void handle_sigterm(int sig) 
{
	if(sig == SIGTERM) {
		puts("sigterm, closing files and exiting...");
		close(input_stream);
		close(output_stream);
		exit(0);
	}
}

int open_input(const char *serial, unsigned long baudrate)
{
	/* open input_stream for read/write */
	struct termios newtio;
	int fd;

	fd = open(serial, O_RDWR | O_NOCTTY);
	if (fd == -1) {
		fprintf(stderr, "Failed to open %s", serial);
		perror("");
		fprintf(stderr, "Make sure the user has permission to open device.\n");
		exit(2);
	}
	fprintf(stdout, "%s opened\n", serial);
	fflush(stdout);

	/* serial port setting */
	bzero(&newtio, sizeof(newtio));
	newtio.c_cflag = CS8 | CLOCAL | CREAD;
	newtio.c_iflag = IGNPAR | IGNBRK;
	cfsetispeed(&newtio, baudrate);
	cfsetospeed(&newtio, baudrate);

	tcflush(fd, TCIFLUSH);
	tcsetattr(fd, TCSANOW, &newtio);

	return fd;
}

