<html>
<!-- 
Copyright 2015 Grip QA

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->
<head>
<title>Quality Zen Configuration</title>
</head>
<body>
<p><strong>Current Configuration:</strong><br></p>
<pre>
<?php include "./cfg.d/qzcfg.cfg"; ?>
</pre>
<p>Looks good&hellip;  &nbsp;
<strong>
<a href="../cgi-bin/qzrun.cgi" target="_blank">Run Quality Zen</a>
</strong>
  &nbsp;<em><font color="green">(Opens in new tab)</font></em><br>
<em>(might take some time, if you're importing data)</em>
</p>
<p><br>Load a new configuration: &nbsp;<br>
 &nbsp; &nbsp; &nbsp; &nbsp;
<em><font color="red">(Hit the "</em><strong>SUBMIT</strong><em>" button to
load your new config!)</font></em></p>
<form action="cfgfile.php" method="post"
enctype="multipart/form-data">
<table>
<tr>
<td>
<label for="file">Filename:</label>
</td>
<td>
<input type="file" name="file" id="file">
</td>
</tr>
<tr>
<td>&nbsp;</td>
<td>
<input type="submit" name="submit" value="SUBMIT">
</td>
</tr>
</table>
</form>

<p><a href="./cfgdoc.html" target="_blank" title="Documentation for the Quality Zen config file">Config File Documentation Page</a>  &nbsp;<em><font color="green">(Opens in new tab)</font></em></p>
</body>
</html>
