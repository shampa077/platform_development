#!/usr/bin/python
# -*- coding: utf-8 -*-

#
# Copyright 2011, The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import sys

def RemoveAnnotation(line):
    if line.find(":") >= 0:
        annotation = line[line.find(":"): line.find(" ", line.find(":"))]
        return line.replace(annotation, "*")
    else:
        return line
        
if __name__ == "__main__":
    externs = []
    lines = open("../../../frameworks/base/opengl/libs/GLES2_dbg/gl2_api_annotated.in").readlines()
    output = open("src/com/android/glesv2debugger/MessageFormatter.java", "w")
    
    i = 0
    output.write(
"""/*
 ** Copyright 2011, The Android Open Source Project
 **
 ** Licensed under the Apache License, Version 2.0 (the "License");
 ** you may not use this file except in compliance with the License.
 ** You may obtain a copy of the License at
 **
 **     http://www.apache.org/licenses/LICENSE-2.0
 **
 ** Unless required by applicable law or agreed to in writing, software
 ** distributed under the License is distributed on an "AS IS" BASIS,
 ** WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 ** See the License for the specific language governing permissions and
 ** limitations under the License.
 */

// auto generated by generate_MessageFormatter_java.py"

package com.android.glesv2debugger;

import java.nio.ByteBuffer;

public class MessageFormatter {

    static String FormatFloats(int count, final ByteBuffer data) {
        if (data.remaining() == 0)
            return "[null]";
        String ret = "[";
        for (int i = 0; i < count; i++)
        {
            ret += Float.intBitsToFloat(Integer.reverseBytes(data.getInt()));
            if (i < count - 1)
                ret += ", ";
        }
        return ret + "]";
    }
    
    static String FormatInts(int count, final ByteBuffer data) {
        if (data.remaining() == 0)
            return "[null]";
        String ret = "[";
        for (int i = 0; i < count; i++)
        {
            ret += Integer.reverseBytes(data.getInt());
            if (i < count - 1)
                ret += ", ";
        }
        return ret + "]";
    }
    
    static String FormatUints(int count, final ByteBuffer data) {
        if (data.remaining() == 0)
            return "[null]";
        String ret = "[";
        for (int i = 0; i < count; i++)
        {
            long bits = Integer.reverseBytes(data.getInt()) & 0xffffffff;
            ret += bits;
            if (i < count - 1)
                ret += ", ";
        }
        return ret + "]";
    }
    
    static String FormatMatrix(int columns, int count, final ByteBuffer data) {
        if (data.remaining() == 0)
            return "[null]";
        String ret = "[";
        for (int i = 0; i < count; i++)
        {
            ret += Float.intBitsToFloat(Integer.reverseBytes(data.getInt()));
            if (i % columns == columns - 1)
                ret += "\\n                                             ";
            else if (i < count - 1)
                ret += ", ";
        }
        return ret + "]";
    }

    public static String Format(final DebuggerMessage.Message msg) {
        String str;
        switch (msg.getFunction()) {
""")
            
    for line in lines:
        if line.find("API_ENTRY(") >= 0: # a function prototype
            returnType = line[0: line.find(" API_ENTRY(")].replace("const ", "")
            functionName = line[line.find("(") + 1: line.find(")")] #extract GL function name
            parameterList = line[line.find(")(") + 2: line.find(") {")]
                        
            parameters = parameterList.split(',')
            paramIndex = 0
            
            formatString = "%s "
            formatArgs = ""
            if returnType != "void":
                if returnType == "GLenum":
                    formatArgs += "GLEnum.valueOf(msg.getRet())"
                elif returnType.find("*") >= 0:
                    formatArgs += '"0x" + Integer.toHexString(msg.getRet())'
                else:
                    formatArgs += "msg.getRet()"
            else:
                formatArgs += '"void"'
            
            #formatString += "%s(" % (functionName)
            formatString += "("
            
            if parameterList == "void":
                parameters = []
            inout = ""
            
            paramNames = []
            
            for parameter in parameters:
                parameter = parameter.replace("const","")
                parameter = parameter.strip()
                paramType = parameter.split(' ')[0]
                paramName = parameter.split(' ')[1]
                annotation = ""
                
                formatString += paramName + "=%s"
                    
                if parameter.find(":") >= 0:
                    assert inout == "" # only one parameter should be annotated
                    inout = paramType.split(":")[2]
                    annotation = paramType.split(":")[1]
                    paramType = paramType.split(":")[0]
                    count = 1
                    countArg = ""
                    if annotation.find("*") >= 0: # [1,n] * param
                        count = int(annotation.split("*")[0])
                        countArg = annotation.split("*")[1]
                        assert countArg in paramNames
                    elif annotation in paramNames:
                        count = 1
                        countArg = annotation
                    elif annotation == "GLstring":
                        annotation = annotation
                    else:
                        count = int(annotation)
                    dataFormatter = ""
                    if paramType == "GLfloat":
                        dataFormatter = "FormatFloats"
                    elif paramType == "GLint":
                        dataFormatter = "FormatInts"
                    elif paramType == "GLuint":
                        dataFormatter = "FormatUints"
                    elif annotation == "GLstring":
                        assert paramType == "GLchar"
                    elif paramType.find("void") >= 0:
                        assert 1
                    else:
                        assert 0
                    if functionName.find("Matrix") >= 0:
                        columns = int(functionName[functionName.find("fv") - 1: functionName.find("fv")])
                        assert columns * columns == count
                        assert countArg != ""
                        assert paramType == "GLfloat"
                        formatArgs += ", FormatMatrix(%d, %d * msg.getArg%d(), msg.getData().asReadOnlyByteBuffer())" % (columns, count, paramNames.index(countArg))
                    elif annotation == "GLstring":
                        formatArgs += ", msg.getData().toStringUtf8()"
                    elif paramType.find("void") >= 0:
                        formatArgs += ', "0x" + Integer.toHexString(msg.getArg%d())' % (paramIndex)
                    elif countArg == "":
                        formatArgs += ", %s(%d, msg.getData().asReadOnlyByteBuffer())" % (dataFormatter, count)
                    else:
                        formatArgs += ", %s(%d * msg.getArg%d(), msg.getData().asReadOnlyByteBuffer())" % (dataFormatter, count, paramNames.index(countArg))
                else:
                    if paramType == "GLfloat" or paramType == "GLclampf":
                        formatArgs += ", Float.intBitsToFloat(msg.getArg%d())" % (paramIndex)
                    elif paramType == "GLenum": 
                        formatArgs += ", GLEnum.valueOf(msg.getArg%d())" % (paramIndex)
                    elif paramType.find("*") >= 0:
                        formatArgs += ', "0x" + Integer.toHexString(msg.getArg%d())' % (paramIndex)
                    else:
                        formatArgs += ", msg.getArg%d()" % (paramIndex)
                if paramIndex < len(parameters) - 1:
                    formatString += ", "
                paramNames.append(paramName)
                paramIndex += 1  

                
            formatString += ")"
             
            output.write("            case %s:\n" % (functionName))
            if line.find("*") >= 0 and (line.find("*") < line.find(":") or line.find("*") > line.rfind(":")):
                sys.stderr.write(line)
                output.write("                // FIXME: this function uses pointers, debugger may send data in msg.data\n")
            output.write('                str = String.format("%s", %s); break;\n' % (formatString, formatArgs))
            

    output.write("""            default:
                str = msg.toString();
        }
        return str;
    }
}""")

'''    print """/*
package GLESv2Debugger;

public class MessageFormatterCustom {

    public static String Format(final DebuggerMessage.Message msg) {
        String str;
        switch (msg.getFunction()) {"""

    for extern in externs:
        print "        case %s" % (extern)
        print "            // TODO:"

print """        default:
            str = msg.toString();
        }
        return str;
    }
}
*/"""    '''
        
        
