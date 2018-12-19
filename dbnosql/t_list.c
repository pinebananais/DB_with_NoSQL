/*
 * Copyright (c) 2009-2012, Salvatore Sanfilippo <antirez at gmail dot com>
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 *   * Redistributions of source code must retain the above copyright notice,
 *     this list of conditions and the following disclaimer.
 *   * Redistributions in binary form must reproduce the above copyright
 *     notice, this list of conditions and the following disclaimer in the
 *     documentation and/or other materials provided with the distribution.
 *   * Neither the name of Redis nor the names of its contributors may be used
 *     to endorse or promote products derived from this software without
 *     specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 */

#include "server.h"

/*-----------------------------------------------------------------------------
 * List API
 *----------------------------------------------------------------------------*/

/* The function pushes an element to the specified list object 'subject',
 * at head or tail position as specified by 'where'.
 *
 * There is no need for the caller to increment the refcount of 'value' as
 * the function takes care of it if needed. */
void listTypePush(robj *subject, robj *value, int where) {
    if (subject->encoding == OBJ_ENCODING_QUICKLIST) {
        int pos = (where == LIST_HEAD) ? QUICKLIST_HEAD : QUICKLIST_TAIL;
        value = getDecodedObject(value);
        size_t len = sdslen(value->ptr);
        quicklistPush(subject->ptr, value->ptr, len, pos);
        decrRefCount(value);
    } else {
        serverPanic("Unknown list encoding");
    }
}

void *listPopSaver(unsigned char *data, unsigned int sz) {
    return createStringObject((char*)data,sz);
}

robj *listTypePop(robj *subject, int where) {
    long long vlong;
    robj *value = NULL;

    int ql_where = where == LIST_HEAD ? QUICKLIST_HEAD : QUICKLIST_TAIL;
    if (subject->encoding == OBJ_ENCODING_QUICKLIST) {
        if (quicklistPopCustom(subject->ptr, ql_where, (unsigned char **)&value,
                               NULL, &vlong, listPopSaver)) {
            if (!value)
                value = createStringObjectFromLongLong(vlong);
        }
    } else {
        serverPanic("Unknown list encoding");
    }
    return value;
}

unsigned long listTypeLength(const robj *subject) {
    if (subject->encoding == OBJ_ENCODING_QUICKLIST) {
        return quicklistCount(subject->ptr);
    } else {
        serverPanic("Unknown list encoding");
    }
}

/* Initialize an iterator at the specified index. */
listTypeIterator *listTypeInitIterator(robj *subject, long index,
                                       unsigned char direction) {
    listTypeIterator *li = zmalloc(sizeof(listTypeIterator));
    li->subject = subject;
    li->encoding = subject->encoding;
    li->direction = direction;
    li->iter = NULL;
    /* LIST_HEAD means start at TAIL and move *towards* head.
     * LIST_TAIL means start at HEAD and move *towards tail. */
    int iter_direction =
        direction == LIST_HEAD ? AL_START_TAIL : AL_START_HEAD;
    if (li->encoding == OBJ_ENCODING_QUICKLIST) {
        li->iter = quicklistGetIteratorAtIdx(li->subject->ptr,
                                             iter_direction, index);
    } else {
        serverPanic("Unknown list encoding");
    }
    return li;
}

/* Clean up the iterator. */
void listTypeReleaseIterator(listTypeIterator *li) {
    zfree(li->iter);
    zfree(li);
}

/* Stores pointer to current the entry in the provided entry structure
 * and advances the position of the iterator. Returns 1 when the current
 * entry is in fact an entry, 0 otherwise. */
int listTypeNext(listTypeIterator *li, listTypeEntry *entry) {
    /* Protect from converting when iterating */
    serverAssert(li->subject->encoding == li->encoding);

    entry->li = li;
    if (li->encoding == OBJ_ENCODING_QUICKLIST) {
        return quicklistNext(li->iter, &entry->entry);
    } else {
        serverPanic("Unknown list encoding");
    }
    return 0;
}

/* Return entry or NULL at the current position of the iterator. */
robj *listTypeGet(listTypeEntry *entry) {
    robj *value = NULL;
    if (entry->li->encoding == OBJ_ENCODING_QUICKLIST) {
        if (entry->entry.value) {
            value = createStringObject((char *)entry->entry.value,
                                       entry->entry.sz);
        } else {
            value = createStringObjectFromLongLong(entry->entry.longval);
        }
    } else {
        serverPanic("Unknown list encoding");
    }
    return value;
}

void listTypeInsert(listTypeEntry *entry, robj *value, int where) {
    if (entry->li->encoding == OBJ_ENCODING_QUICKLIST) {
        value = getDecodedObject(value);
        sds str = value->ptr;
        size_t len = sdslen(str);
        if (where == LIST_TAIL) {
            quicklistInsertAfter((quicklist *)entry->entry.quicklist,
                                 &entry->entry, str, len);
        } else if (where == LIST_HEAD) {
            quicklistInsertBefore((quicklist *)entry->entry.quicklist,
                                  &entry->entry, str, len);
        }
        decrRefCount(value);
    } else {
        serverPanic("Unknown list encoding");
    }
}

/* Compare the given object with the entry at the current position. */
int listTypeEqual(listTypeEntry *entry, robj *o) {
    if (entry->li->encoding == OBJ_ENCODING_QUICKLIST) {
        serverAssertWithInfo(NULL,o,sdsEncodedObject(o));
        return quicklistCompare(entry->entry.zi,o->ptr,sdslen(o->ptr));
    } else {
        serverPanic("Unknown list encoding");
    }
}

/* Delete the element pointed to. */
void listTypeDelete(listTypeIterator *iter, listTypeEntry *entry) {
    if (entry->li->encoding == OBJ_ENCODING_QUICKLIST) {
        quicklistDelEntry(iter->iter, &entry->entry);
    } else {
        serverPanic("Unknown list encoding");
    }
}

/* Create a quicklist from a single ziplist */
void listTypeConvert(robj *subject, int enc) {
    serverAssertWithInfo(NULL,subject,subject->type==OBJ_LIST);
    serverAssertWithInfo(NULL,subject,subject->encoding==OBJ_ENCODING_ZIPLIST);

    if (enc == OBJ_ENCODING_QUICKLIST) {
        size_t zlen = server.list_max_ziplist_size;
        int depth = server.list_compress_depth;
        subject->ptr = quicklistCreateFromZiplist(zlen, depth, subject->ptr);
        subject->encoding = OBJ_ENCODING_QUICKLIST;
    } else {
        serverPanic("Unsupported list conversion");
    }
}

/*-----------------------------------------------------------------------------
 * List Commands
 *----------------------------------------------------------------------------*/

void pushGenericCommand(client *c, int where) {
    int j, pushed = 0;
    robj *lobj = lookupKeyWrite(c->db,c->argv[1]);

    if (lobj && lobj->type != OBJ_LIST) {
        addReply(c,shared.wrongtypeerr);
        return;
    }

    for (j = 2; j < c->argc; j++) {
        if (!lobj) {
            lobj = createQuicklistObject();
            quicklistSetOptions(lobj->ptr, server.list_max_ziplist_size,
                                server.list_compress_depth);
            dbAdd(c->db,c->argv[1],lobj);
        }
        listTypePush(lobj,c->argv[j],where);
        pushed++;
    }
    addReplyLongLong(c, (lobj ? listTypeLength(lobj) : 0));
    if (pushed) {
        char *event = (where == LIST_HEAD) ? "lpush" : "rpush";

        signalModifiedKey(c->db,c->argv[1]);
        notifyKeyspaceEvent(NOTIFY_LIST,event,c->argv[1],c->db->id);
    }
    server.dirty += pushed;
}

void lpushCommand(client *c) {
    pushGenericCommand(c,LIST_HEAD);
}

void rpushCommand(client *c) {
    pushGenericCommand(c,LIST_TAIL);
}

void pushxGenericCommand(client *c, int where) {
    int j, pushed = 0;
    robj *subject;

    if ((subject = lookupKeyWriteOrReply(c,c->argv[1],shared.czero)) == NULL ||
        checkType(c,subject,OBJ_LIST)) return;

    for (j = 2; j < c->argc; j++) {
        listTypePush(subject,c->argv[j],where);
        pushed++;
    }

    addReplyLongLong(c,listTypeLength(subject));

    if (pushed) {
        char *event = (where == LIST_HEAD) ? "lpush" : "rpush";
        signalModifiedKey(c->db,c->argv[1]);
        notifyKeyspaceEvent(NOTIFY_LIST,event,c->argv[1],c->db->id);
    }
    server.dirty += pushed;
}

void lpushxCommand(client *c) {
    pushxGenericCommand(c,LIST_HEAD);
}

void rpushxCommand(client *c) {
    pushxGenericCommand(c,LIST_TAIL);
}

void linsertCommand(client *c) {
    int where;
    robj *subject;
    listTypeIterator *iter;
    listTypeEntry entry;
    int inserted = 0;

    if (strcasecmp(c->argv[2]->ptr,"after") == 0) {
        where = LIST_TAIL;
    } else if (strcasecmp(c->argv[2]->ptr,"before") == 0) {
        where = LIST_HEAD;
    } else {
        addReply(c,shared.syntaxerr);
        return;
    }

    if ((subject = lookupKeyWriteOrReply(c,c->argv[1],shared.czero)) == NULL ||
        checkType(c,subject,OBJ_LIST)) return;

    /* Seek pivot from head to tail */
    iter = listTypeInitIterator(subject,0,LIST_TAIL);
    while (listTypeNext(iter,&entry)) {
        if (listTypeEqual(&entry,c->argv[3])) {
            listTypeInsert(&entry,c->argv[4],where);
            inserted = 1;
            break;
        }
    }
    listTypeReleaseIterator(iter);

    if (inserted) {
        signalModifiedKey(c->db,c->argv[1]);
        notifyKeyspaceEvent(NOTIFY_LIST,"linsert",
                            c->argv[1],c->db->id);
        server.dirty++;
    } else {
        /* Notify client of a failed insert */
        addReply(c,shared.cnegone);
        return;
    }

    addReplyLongLong(c,listTypeLength(subject));
}

void llenCommand(client *c) {
    robj *o = lookupKeyReadOrReply(c,c->argv[1],shared.czero);
    if (o == NULL || checkType(c,o,OBJ_LIST)) return;
    addReplyLongLong(c,listTypeLength(o));
}

void lindexCommand(client *c) {
    robj *o = lookupKeyReadOrReply(c,c->argv[1],shared.nullbulk);
    if (o == NULL || checkType(c,o,OBJ_LIST)) return;
    long index;
    robj *value = NULL;

    if ((getLongFromObjectOrReply(c, c->argv[2], &index, NULL) != C_OK))
        return;

    if (o->encoding == OBJ_ENCODING_QUICKLIST) {
        quicklistEntry entry;
        if (quicklistIndex(o->ptr, index, &entry)) {
            if (entry.value) {
                value = createStringObject((char*)entry.value,entry.sz);
            } else {
                value = createStringObjectFromLongLong(entry.longval);
            }
            addReplyBulk(c,value);
            decrRefCount(value);
        } else {
            addReply(c,shared.nullbulk);
        }
    } else {
        serverPanic("Unknown list encoding");
    }
}

void lsetCommand(client *c) {
    robj *o = lookupKeyWriteOrReply(c,c->argv[1],shared.nokeyerr);
    if (o == NULL || checkType(c,o,OBJ_LIST)) return;
    long index;
    robj *value = c->argv[3];

    if ((getLongFromObjectOrReply(c, c->argv[2], &index, NULL) != C_OK))
        return;

    if (o->encoding == OBJ_ENCODING_QUICKLIST) {
        quicklist *ql = o->ptr;
        int replaced = quicklistReplaceAtIndex(ql, index,
                                               value->ptr, sdslen(value->ptr));
        if (!replaced) {
            addReply(c,shared.outofrangeerr);
        } else {
            addReply(c,shared.ok);
            signalModifiedKey(c->db,c->argv[1]);
            notifyKeyspaceEvent(NOTIFY_LIST,"lset",c->argv[1],c->db->id);
            server.dirty++;
        }
    } else {
        serverPanic("Unknown list encoding");
    }
}

void popGenericCommand(client *c, int where) {
    robj *o = lookupKeyWriteOrReply(c,c->argv[1],shared.nullbulk);
    if (o == NULL || checkType(c,o,OBJ_LIST)) return;

    robj *value = listTypePop(o,where);
    if (value == NULL) {
        addReply(c,shared.nullbulk);
    } else {
        char *event = (where == LIST_HEAD) ? "lpop" : "rpop";

        addReplyBulk(c,value);
        decrRefCount(value);
        notifyKeyspaceEvent(NOTIFY_LIST,event,c->argv[1],c->db->id);
        if (listTypeLength(o) == 0) {
            notifyKeyspaceEvent(NOTIFY_GENERIC,"del",
                                c->argv[1],c->db->id);
            dbDelete(c->db,c->argv[1]);
        }
        signalModifiedKey(c->db,c->argv[1]);
        server.dirty++;
    }
}

void lpopCommand(client *c) {
    popGenericCommand(c,LIST_HEAD);
}

void rpopCommand(client *c) {
    popGenericCommand(c,LIST_TAIL);
}

void lrangeCommand(client *c) {
    robj *o;
    long start, end, llen, rangelen;

    if ((getLongFromObjectOrReply(c, c->argv[2], &start, NULL) != C_OK) ||
        (getLongFromObjectOrReply(c, c->argv[3], &end, NULL) != C_OK)) return;

    if ((o = lookupKeyReadOrReply(c,c->argv[1],shared.emptymultibulk)) == NULL
         || checkType(c,o,OBJ_LIST)) return;
    llen = listTypeLength(o);

    /* convert negative indexes */
    if (start < 0) start = llen+start;
    if (end < 0) end = llen+end;
    if (start < 0) start = 0;

    /* Invariant: start >= 0, so this test will be true when end < 0.
     * The range is empty when start > end or start >= length. */
    if (start > end || start >= llen) {
        addReply(c,shared.emptymultibulk);
        return;
    }
    if (end >= llen) end = llen-1;
    rangelen = (end-start)+1;

    /* Return the result in form of a multi-bulk reply */
    addReplyMultiBulkLen(c,rangelen);
    if (o->encoding == OBJ_ENCODING_QUICKLIST) {
        listTypeIterator *iter = listTypeInitIterator(o, start, LIST_TAIL);

        while(rangelen--) {
            listTypeEntry entry;
            listTypeNext(iter, &entry);
            quicklistEntry *qe = &entry.entry;
            if (qe->value) {
                addReplyBulkCBuffer(c,qe->value,qe->sz);
            } else {
                addReplyBulkLongLong(c,qe->longval);
            }
        }
        listTypeReleaseIterator(iter);
    } else {
        serverPanic("List encoding is not QUICKLIST!");
    }
}

// modified by YIS 12-12 

long compare_value(long lhs, char *oper, long rhs){
	printf("in function : %ld %s %ld\n", lhs, oper, rhs);
	if(strcmp(oper, "<") == 0) return lhs < rhs;
	if(strcmp(oper, ">") == 0) return lhs > rhs;
	if(strcmp(oper, "=") == 0) return lhs == rhs;
	if(strcmp(oper, "!=") == 0) return lhs != rhs;
	if(strcmp(oper, "<=") == 0) return lhs <= rhs;
	if(strcmp(oper, ">=") == 0) return lhs >= rhs;
}

long pattern_match(const char *s, const char *p) {
    if(*s == 0 && *p == 0) return 1;
    if(*p == 0) return 0;
    if(*p == 37 && *s == 0) return pattern_match(s, p + 1);
    if(*p == 37) return pattern_match(s, p + 1) || pattern_match(s + 1, p);
    if(*p == '_' && *s == 0) return 0;
    if(*p == '_') return pattern_match(s + 1, p + 1);
    if(*s == 0) return 0;
	return (*s == *p) && pattern_match(s + 1, p + 1);
} 

long compare_str(char *lhs, char *oper, char *rhs){
	printf("in function : %s %s %s\n", lhs, oper, rhs);
	if(strcmp(oper, "=") == 0) return !(strcmp(lhs, rhs));
	if(strcmp(oper, "!=") == 0) return strcmp(lhs, rhs);
	if(strcmp(oper, "LIKE") == 0) return pattern_match(lhs, rhs);
}

long str2int(char *str){
	long res = 0;
	long i;
	for(i = 0; str[i] != 0; i++){
		res *= 10;
		res += str[i] - '0';
	}
	return res;
}

// multipredicate

void mylrangeCommand(client *c) { // single predicate
    robj *o;
    robj *oh;
    hashTypeIterator *hi;
    long start, end, llen, rangelen, i;
    if ((oh = lookupKeyReadOrReply(c,c->argv[1],shared.emptymultibulk)) == NULL
         || checkType(c,oh,OBJ_HASH)) return;
    if ((o = lookupKeyReadOrReply(c,c->argv[2],shared.emptymultibulk)) == NULL
         || checkType(c,o,OBJ_LIST)) return;
    llen = listTypeLength(o); // # of total table cells
    printf("%ld\n", c->argc);
    long argcnt = 3;
    long **stack = (long**)malloc(sizeof(long*)*10);
    long top = -1;
    long cursz = 10;
    long rowlen = 0;
    while (argcnt < c->argc){
    	if(strcmp((char*)c->argv[argcnt]->ptr, "AND") == 0){
    		long *fi = stack[top--];
    		long *se = stack[top--];
    		long fisz = fi[0];
    		long fidx = 1;
    		long sesz = se[0];
    		long sedx = 1;
    		long *res = (long*)malloc(sizeof(long) * 10);
    		long rescnt = 1;
    		while(fidx <= fisz && sedx <= sesz){
    			if(fi[fidx] == se[sedx]){
    				res[rescnt++] = fi[fidx];
    				if(rescnt % 10 == 0) res = (long*)realloc(res, sizeof(long)*(rescnt + 10));
    				fidx++;
    				sedx++;
    			}
    			else if(fi[fidx] > se[sedx]) sedx++;
    			else if(fi[fidx] < se[sedx]) fidx++;
    		}
    		free(fi), free(se);
    		res[0] = rescnt - 1;
    		stack[++top] = res;
    		if(top == cursz - 1){
    			stack = (long**)realloc(stack, sizeof(long*)*(cursz+10));
    			cursz += 10;
    		}
    		argcnt++;
    		continue;
    	}
    	else if(strcmp((char*)c->argv[argcnt]->ptr, "OR") == 0){
    		long *fi = stack[top--];
    		long *se = stack[top--];
    		long fisz = fi[0];
    		long fidx = 1;
    		long sesz = se[0];
    		long sedx = 1;
    		printf("size : %ld %ld\n", fisz, sesz);
    		printf("size : %ld %ld\n", fi[1], se[1]);
    		long *res = (long*)malloc(sizeof(long) * 10);
    		long rescnt = 1;
    		while(fidx <= fisz && sedx <= sesz){
    			if(fi[fidx] == se[sedx]){
    				res[rescnt++] = fi[fidx];
    				if(rescnt % 10 == 0) res = (long*)realloc(res, sizeof(long)*(rescnt + 10));
    				fidx++;
    				sedx++;
    			}
    			else if(fi[fidx] > se[sedx]){
    				res[rescnt++] = se[sedx];
					if(rescnt % 10 == 0) res = (long*)realloc(res, sizeof(long)*(rescnt + 10));
					sedx++;
    			}
    			else if(fi[fidx] < se[sedx]){
    				res[rescnt++] = fi[fidx];
					if(rescnt % 10 == 0) res = (long*)realloc(res, sizeof(long)*(rescnt + 10));
					fidx++;
    			}
    		}
    		while(fidx <= fisz){
    			res[rescnt++] = fi[fidx];
				if(rescnt % 10 == 0) res = (long*)realloc(res, sizeof(long)*(rescnt + 10));
				fidx++;
    		}
    		while(sedx <= sesz){
    			res[rescnt++] = se[sedx];
				if(rescnt % 10 == 0) res = (long*)realloc(res, sizeof(long)*(rescnt + 10));
				sedx++;
    		}
    		free(fi), free(se);
    		res[0] = rescnt - 1;
    		stack[++top] = res;
    		if(top == cursz - 1){
    			stack = (long**)realloc(stack, sizeof(long*)*(cursz+10));
    			cursz += 10;
    		}
    		argcnt++;
    		continue;
    	}
		char *arg1 = (char*)c->argv[argcnt++]->ptr;
		char *arg2 = (char*)c->argv[argcnt++]->ptr;
		char *arg3 = (char*)c->argv[argcnt++]->ptr;
		char *arg4 = (char*)c->argv[argcnt++]->ptr;
		long *index_arr = (long*)malloc(sizeof(long) * 10); // result list
		long index = 0; // index # of target attr
		long attr_count = 0; // colomn count
		long count = 1;
		
		hi = hashTypeInitIterator(oh);
		while (hashTypeNext(hi) != C_ERR) {
			unsigned char *vstr = NULL;
			unsigned char rstr[128];
		    unsigned int vlen = UINT_MAX;
		    long long vll = LLONG_MAX;
			int what;
		    hashTypeCurrentFromZiplist(hi, OBJ_HASH_KEY, &vstr, &vlen, &vll);
		    strncpy(rstr, vstr, vlen);
		    rstr[vlen] = '\0';
		    if(strcmp(arg1, rstr) == 0) index = attr_count;
		    attr_count++;
		}

		hashTypeReleaseIterator(hi);
		rowlen = llen / attr_count; // # of rows
		if (o->encoding == OBJ_ENCODING_QUICKLIST) {
			 for(i = 0; i < rowlen; i++){
				quicklistEntry entry;
				int look = i * attr_count + index; // index of each target attr
				if (quicklistIndex(o->ptr, look, &entry)) {
				    long val = entry.longval;
					if(arg4[0] == '1'){
						if(compare_value(val, arg2, str2int(arg3))){ // if condition satisfied
							index_arr[count++] = i; // accept to result list
						}
					}
					else{
						char buff[128] = {0,};
						strncpy(buff, entry.value, entry.sz);
						if(compare_str(buff, arg2, arg3)){
							index_arr[count++] = i; // accept to result list
						}
					}
				} else {
				    addReply(c,shared.nullbulk);
				}
				if(count % 10 == 0){ // reallocate result list when over its capacity
					index_arr = (long*)realloc(index_arr, sizeof(long)*(count + 10));
				}
			 }
		} else {
		    serverPanic("Unknown list encoding");
		}
		index_arr[0] = count - 1; // every stack element has its size in 0'th index
		stack[++top] = index_arr;
		if(top == cursz - 1){
			stack = (long**)realloc(stack, sizeof(long*)*(cursz+10));
			cursz += 10;
		}
	}
	printf("top val : %ld :\n", top);
	long count = stack[0][0];
    addReplyMultiBulkLen(c, count); // write total number
    for(i = 1; i <= count; i++) addReplyLongLong(c, stack[0][i]); // write each number in result list
    free(stack[0]);
    free(stack);
}

// multi predicate end

void mylrangeCommand_deprecated(client *c) { // single predicate
	printf("Entered\n");
    robj *o;
    robj *oh;
    hashTypeIterator *hi;
    long start, end, llen, rangelen, i;
    if ((oh = lookupKeyReadOrReply(c,c->argv[1],shared.emptymultibulk)) == NULL
         || checkType(c,oh,OBJ_HASH)) return;
    if ((o = lookupKeyReadOrReply(c,c->argv[2],shared.emptymultibulk)) == NULL
         || checkType(c,o,OBJ_LIST)) return;
    llen = listTypeLength(o); // # of total table cells
    printf("%ld\n", c->argc);
	char *arg1 = (char*)c->argv[3]->ptr;
	char *arg2 = (char*)c->argv[4]->ptr;
	char *arg3 = (char*)c->argv[5]->ptr;
	char *arg4 = (char*)c->argv[6]->ptr;
	printf("first arg : %s\n", arg1);
    long *index_arr = (long*)malloc(sizeof(long) * 10); // result list
    long index = 0; // index # of target attr
    long attr_count = 0; // colomn count
    long count = 0;
    
    hi = hashTypeInitIterator(oh);
    while (hashTypeNext(hi) != C_ERR) {
    	unsigned char *vstr = NULL;
    	unsigned char rstr[128];
        unsigned int vlen = UINT_MAX;
        long long vll = LLONG_MAX;
	int what;
        hashTypeCurrentFromZiplist(hi, OBJ_HASH_KEY, &vstr, &vlen, &vll);
        strncpy(rstr, vstr, vlen);
        rstr[vlen] = '\0';
        if(strcmp(arg1, rstr) == 0) index = attr_count;
        attr_count++;
    }

    hashTypeReleaseIterator(hi);
    llen /= attr_count; // # of rows
    if (o->encoding == OBJ_ENCODING_QUICKLIST) {
		 for(i = 0; i < llen; i++){
		    quicklistEntry entry;
		    int look = i * attr_count + index; // index of each target attr
		    if (quicklistIndex(o->ptr, look, &entry)) {
		        long val = entry.longval;
		        printf("%s\n", arg3);
				if(arg4[0] == '1'){
				    if(compare_value(val, arg2, str2int(arg3))){ // if condition satisfied
				    	index_arr[count++] = i; // accept to result list
				    }
				}
				else{
					char buff[128] = {0,};
					strncpy(buff, entry.value, entry.sz);
					if(compare_str(buff, arg2, arg3)){
						index_arr[count++] = i; // accept to result list
					}
				}
		    } else {
		        addReply(c,shared.nullbulk);
		    }
		    if(count % 10 == 0 && count > 0){ // reallocate result list when over its capacity
		    	index_arr = (long*)realloc(index_arr, sizeof(long)*count*2);
		    }
		 }
    } else {
        serverPanic("Unknown list encoding");
    }
    addReplyMultiBulkLen(c, count); // write total number
    for(i = 0; i < count; i++) addReplyLongLong(c, index_arr[i]); // write each number in result list
    free(index_arr);
}

// end

void ltrimCommand(client *c) {
    robj *o;
    long start, end, llen, ltrim, rtrim;

    if ((getLongFromObjectOrReply(c, c->argv[2], &start, NULL) != C_OK) ||
        (getLongFromObjectOrReply(c, c->argv[3], &end, NULL) != C_OK)) return;

    if ((o = lookupKeyWriteOrReply(c,c->argv[1],shared.ok)) == NULL ||
        checkType(c,o,OBJ_LIST)) return;
    llen = listTypeLength(o);

    /* convert negative indexes */
    if (start < 0) start = llen+start;
    if (end < 0) end = llen+end;
    if (start < 0) start = 0;

    /* Invariant: start >= 0, so this test will be true when end < 0.
     * The range is empty when start > end or start >= length. */
    if (start > end || start >= llen) {
        /* Out of range start or start > end result in empty list */
        ltrim = llen;
        rtrim = 0;
    } else {
        if (end >= llen) end = llen-1;
        ltrim = start;
        rtrim = llen-end-1;
    }

    /* Remove list elements to perform the trim */
    if (o->encoding == OBJ_ENCODING_QUICKLIST) {
        quicklistDelRange(o->ptr,0,ltrim);
        quicklistDelRange(o->ptr,-rtrim,rtrim);
    } else {
        serverPanic("Unknown list encoding");
    }

    notifyKeyspaceEvent(NOTIFY_LIST,"ltrim",c->argv[1],c->db->id);
    if (listTypeLength(o) == 0) {
        dbDelete(c->db,c->argv[1]);
        notifyKeyspaceEvent(NOTIFY_GENERIC,"del",c->argv[1],c->db->id);
    }
    signalModifiedKey(c->db,c->argv[1]);
    server.dirty++;
    addReply(c,shared.ok);
}

void lremCommand(client *c) {
    robj *subject, *obj;
    obj = c->argv[3];
    long toremove;
    long removed = 0;

    if ((getLongFromObjectOrReply(c, c->argv[2], &toremove, NULL) != C_OK))
        return;

    subject = lookupKeyWriteOrReply(c,c->argv[1],shared.czero);
    if (subject == NULL || checkType(c,subject,OBJ_LIST)) return;

    listTypeIterator *li;
    if (toremove < 0) {
        toremove = -toremove;
        li = listTypeInitIterator(subject,-1,LIST_HEAD);
    } else {
        li = listTypeInitIterator(subject,0,LIST_TAIL);
    }

    listTypeEntry entry;
    while (listTypeNext(li,&entry)) {
        if (listTypeEqual(&entry,obj)) {
            listTypeDelete(li, &entry);
            server.dirty++;
            removed++;
            if (toremove && removed == toremove) break;
        }
    }
    listTypeReleaseIterator(li);

    if (removed) {
        signalModifiedKey(c->db,c->argv[1]);
        notifyKeyspaceEvent(NOTIFY_GENERIC,"lrem",c->argv[1],c->db->id);
    }

    if (listTypeLength(subject) == 0) {
        dbDelete(c->db,c->argv[1]);
        notifyKeyspaceEvent(NOTIFY_GENERIC,"del",c->argv[1],c->db->id);
    }

    addReplyLongLong(c,removed);
}

/* This is the semantic of this command:
 *  RPOPLPUSH srclist dstlist:
 *    IF LLEN(srclist) > 0
 *      element = RPOP srclist
 *      LPUSH dstlist element
 *      RETURN element
 *    ELSE
 *      RETURN nil
 *    END
 *  END
 *
 * The idea is to be able to get an element from a list in a reliable way
 * since the element is not just returned but pushed against another list
 * as well. This command was originally proposed by Ezra Zygmuntowicz.
 */

void rpoplpushHandlePush(client *c, robj *dstkey, robj *dstobj, robj *value) {
    /* Create the list if the key does not exist */
    if (!dstobj) {
        dstobj = createQuicklistObject();
        quicklistSetOptions(dstobj->ptr, server.list_max_ziplist_size,
                            server.list_compress_depth);
        dbAdd(c->db,dstkey,dstobj);
    }
    signalModifiedKey(c->db,dstkey);
    listTypePush(dstobj,value,LIST_HEAD);
    notifyKeyspaceEvent(NOTIFY_LIST,"lpush",dstkey,c->db->id);
    /* Always send the pushed value to the client. */
    addReplyBulk(c,value);
}

void rpoplpushCommand(client *c) {
    robj *sobj, *value;
    if ((sobj = lookupKeyWriteOrReply(c,c->argv[1],shared.nullbulk)) == NULL ||
        checkType(c,sobj,OBJ_LIST)) return;

    if (listTypeLength(sobj) == 0) {
        /* This may only happen after loading very old RDB files. Recent
         * versions of Redis delete keys of empty lists. */
        addReply(c,shared.nullbulk);
    } else {
        robj *dobj = lookupKeyWrite(c->db,c->argv[2]);
        robj *touchedkey = c->argv[1];

        if (dobj && checkType(c,dobj,OBJ_LIST)) return;
        value = listTypePop(sobj,LIST_TAIL);
        /* We saved touched key, and protect it, since rpoplpushHandlePush
         * may change the client command argument vector (it does not
         * currently). */
        incrRefCount(touchedkey);
        rpoplpushHandlePush(c,c->argv[2],dobj,value);

        /* listTypePop returns an object with its refcount incremented */
        decrRefCount(value);

        /* Delete the source list when it is empty */
        notifyKeyspaceEvent(NOTIFY_LIST,"rpop",touchedkey,c->db->id);
        if (listTypeLength(sobj) == 0) {
            dbDelete(c->db,touchedkey);
            notifyKeyspaceEvent(NOTIFY_GENERIC,"del",
                                touchedkey,c->db->id);
        }
        signalModifiedKey(c->db,touchedkey);
        decrRefCount(touchedkey);
        server.dirty++;
        if (c->cmd->proc == brpoplpushCommand) {
            rewriteClientCommandVector(c,3,shared.rpoplpush,c->argv[1],c->argv[2]);
        }
    }
}

/*-----------------------------------------------------------------------------
 * Blocking POP operations
 *----------------------------------------------------------------------------*/

/* This is a helper function for handleClientsBlockedOnLists(). It's work
 * is to serve a specific client (receiver) that is blocked on 'key'
 * in the context of the specified 'db', doing the following:
 *
 * 1) Provide the client with the 'value' element.
 * 2) If the dstkey is not NULL (we are serving a BRPOPLPUSH) also push the
 *    'value' element on the destination list (the LPUSH side of the command).
 * 3) Propagate the resulting BRPOP, BLPOP and additional LPUSH if any into
 *    the AOF and replication channel.
 *
 * The argument 'where' is LIST_TAIL or LIST_HEAD, and indicates if the
 * 'value' element was popped fron the head (BLPOP) or tail (BRPOP) so that
 * we can propagate the command properly.
 *
 * The function returns C_OK if we are able to serve the client, otherwise
 * C_ERR is returned to signal the caller that the list POP operation
 * should be undone as the client was not served: This only happens for
 * BRPOPLPUSH that fails to push the value to the destination key as it is
 * of the wrong type. */
int serveClientBlockedOnList(client *receiver, robj *key, robj *dstkey, redisDb *db, robj *value, int where)
{
    robj *argv[3];

    if (dstkey == NULL) {
        /* Propagate the [LR]POP operation. */
        argv[0] = (where == LIST_HEAD) ? shared.lpop :
                                          shared.rpop;
        argv[1] = key;
        propagate((where == LIST_HEAD) ?
            server.lpopCommand : server.rpopCommand,
            db->id,argv,2,PROPAGATE_AOF|PROPAGATE_REPL);

        /* BRPOP/BLPOP */
        addReplyMultiBulkLen(receiver,2);
        addReplyBulk(receiver,key);
        addReplyBulk(receiver,value);
        
        /* Notify event. */
        char *event = (where == LIST_HEAD) ? "lpop" : "rpop";
        notifyKeyspaceEvent(NOTIFY_LIST,event,key,receiver->db->id);
    } else {
        /* BRPOPLPUSH */
        robj *dstobj =
            lookupKeyWrite(receiver->db,dstkey);
        if (!(dstobj &&
             checkType(receiver,dstobj,OBJ_LIST)))
        {
            /* Propagate the RPOP operation. */
            argv[0] = shared.rpop;
            argv[1] = key;
            propagate(server.rpopCommand,
                db->id,argv,2,
                PROPAGATE_AOF|
                PROPAGATE_REPL);
            rpoplpushHandlePush(receiver,dstkey,dstobj,
                value);
            /* Propagate the LPUSH operation. */
            argv[0] = shared.lpush;
            argv[1] = dstkey;
            argv[2] = value;
            propagate(server.lpushCommand,
                db->id,argv,3,
                PROPAGATE_AOF|
                PROPAGATE_REPL);

            /* Notify event ("lpush" was notified by rpoplpushHandlePush). */
            notifyKeyspaceEvent(NOTIFY_LIST,"rpop",key,receiver->db->id);
        } else {
            /* BRPOPLPUSH failed because of wrong
             * destination type. */
            return C_ERR;
        }
    }
    return C_OK;
}

/* Blocking RPOP/LPOP */
void blockingPopGenericCommand(client *c, int where) {
    robj *o;
    mstime_t timeout;
    int j;

    if (getTimeoutFromObjectOrReply(c,c->argv[c->argc-1],&timeout,UNIT_SECONDS)
        != C_OK) return;

    for (j = 1; j < c->argc-1; j++) {
        o = lookupKeyWrite(c->db,c->argv[j]);
        if (o != NULL) {
            if (o->type != OBJ_LIST) {
                addReply(c,shared.wrongtypeerr);
                return;
            } else {
                if (listTypeLength(o) != 0) {
                    /* Non empty list, this is like a non normal [LR]POP. */
                    char *event = (where == LIST_HEAD) ? "lpop" : "rpop";
                    robj *value = listTypePop(o,where);
                    serverAssert(value != NULL);

                    addReplyMultiBulkLen(c,2);
                    addReplyBulk(c,c->argv[j]);
                    addReplyBulk(c,value);
                    decrRefCount(value);
                    notifyKeyspaceEvent(NOTIFY_LIST,event,
                                        c->argv[j],c->db->id);
                    if (listTypeLength(o) == 0) {
                        dbDelete(c->db,c->argv[j]);
                        notifyKeyspaceEvent(NOTIFY_GENERIC,"del",
                                            c->argv[j],c->db->id);
                    }
                    signalModifiedKey(c->db,c->argv[j]);
                    server.dirty++;

                    /* Replicate it as an [LR]POP instead of B[LR]POP. */
                    rewriteClientCommandVector(c,2,
                        (where == LIST_HEAD) ? shared.lpop : shared.rpop,
                        c->argv[j]);
                    return;
                }
            }
        }
    }

    /* If we are inside a MULTI/EXEC and the list is empty the only thing
     * we can do is treating it as a timeout (even with timeout 0). */
    if (c->flags & CLIENT_MULTI) {
        addReply(c,shared.nullmultibulk);
        return;
    }

    /* If the list is empty or the key does not exists we must block */
    blockForKeys(c,BLOCKED_LIST,c->argv + 1,c->argc - 2,timeout,NULL,NULL);
}

void blpopCommand(client *c) {
    blockingPopGenericCommand(c,LIST_HEAD);
}

void brpopCommand(client *c) {
    blockingPopGenericCommand(c,LIST_TAIL);
}

void brpoplpushCommand(client *c) {
    mstime_t timeout;

    if (getTimeoutFromObjectOrReply(c,c->argv[3],&timeout,UNIT_SECONDS)
        != C_OK) return;

    robj *key = lookupKeyWrite(c->db, c->argv[1]);

    if (key == NULL) {
        if (c->flags & CLIENT_MULTI) {
            /* Blocking against an empty list in a multi state
             * returns immediately. */
            addReply(c, shared.nullbulk);
        } else {
            /* The list is empty and the client blocks. */
            blockForKeys(c,BLOCKED_LIST,c->argv + 1,1,timeout,c->argv[2],NULL);
        }
    } else {
        if (key->type != OBJ_LIST) {
            addReply(c, shared.wrongtypeerr);
        } else {
            /* The list exists and has elements, so
             * the regular rpoplpushCommand is executed. */
            serverAssertWithInfo(c,key,listTypeLength(key) > 0);
            rpoplpushCommand(c);
        }
    }
}
