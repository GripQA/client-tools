<html>
<body>
<?php
/*
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
*/
$allowedExts = array("cfg");
$extension = end(explode(".", $_FILES["file"]["name"]));
//echo "File type:  " . $_FILES["file"]["type"];
if (($_FILES["file"]["type"] == "application/octet-stream")
&& ($_FILES["file"]["size"] < 20000)
&& in_array($extension, $allowedExts))
  {
  if ($_FILES["file"]["error"] > 0)
    {
    echo "Return Code: " . $_FILES["file"]["error"] . "<br>";
    }
  else
    {
    echo "Upload: " . $_FILES["file"]["name"] . "<br>";
    echo "Type: " . $_FILES["file"]["type"] . "<br>";
    echo "Size: " . ($_FILES["file"]["size"] / 1024) . " kB<br>";
    echo "Temp file: " . $_FILES["file"]["tmp_name"] . "<br>";
    
    $cfgDir = "cfg.d/";
    $cfgFile = "qzcfg.cfg";

    // if (file_exists("cfgs/" . $_FILES["file"]["name"]))
    if (file_exists($cfgDir . $cfgFile))
      {
      // echo $_FILES["file"]["name"] . " already exists. Will overwrite.";
      echo "Note: Updating configuration information.<br>";
      }
    if (move_uploaded_file($_FILES["file"]["tmp_name"], $cfgDir . $cfgFile))
      {
        echo "Successfully updated.<br>New Configuration:<br>";
        echo "<pre>";
        include $cfgDir . $cfgFile;
        echo "</pre>";
      }
    else
      {
        echo "ERROR:  Unable to update configuration. File move failed.<br>";
      }
      // to keep name:  ".cfg.d/" . $_FILES["file"]["name"]);
    // echo "Stored in: " . ".cfg.d/" . $_FILES["file"]["name"];
    }
  }
else
  {
  echo "Invalid file";
  }
?>
<p>Looks good&hellip;  &nbsp;<strong>
<a href="../cgi-bin/qzrun.cgi" target="_blank">Run Quality Zen</a></strong>  &nbsp;<em><font color="green">(Opens in new tab)</font></em><br>
<em>(might take some time, if you're importing data)</em></p>
<p><a href="./loadcfg.php">Back to configuration</a></p>
</body>
</html>
