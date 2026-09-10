import os
import re

directory = '/home/parth.dave/v19/custom_modules/Pertrogulf'

# Attributes that should be True/False instead of 1/0
attrs_to_fix = [
    'invisible', 'readonly', 'required', 'force_save', 'nolabel', 'nolable', 
    'column_invisible', 'sample', 'multi_edit'
]

# Create regex to match ` attr="1"` and ` attr="0"`
regex_1 = re.compile(r'\b(' + '|'.join(attrs_to_fix) + r')\s*=\s*["\']1["\']')
regex_0 = re.compile(r'\b(' + '|'.join(attrs_to_fix) + r')\s*=\s*["\']0["\']')
regex_attr_1 = re.compile(r'<attribute\s+name=["\'](' + '|'.join(attrs_to_fix) + r')["\']\s*>\s*1\s*</attribute>')
regex_attr_0 = re.compile(r'<attribute\s+name=["\'](' + '|'.join(attrs_to_fix) + r')["\']\s*>\s*0\s*</attribute>')

# Create regex to fix nolable to nolabel
regex_nolable = re.compile(r'\bnolable\s*=')

for root, dirs, files in os.walk(directory):
    for file in files:
        if file.endswith('.xml'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r+', encoding='utf-8') as f:
                content = f.read()
                original_content = content
                
                # Replace 1 -> True
                content = regex_1.sub(r'\1="True"', content)
                # Replace 0 -> False
                content = regex_0.sub(r'\1="False"', content)
                # Replace <attribute name="...">1</attribute>
                content = regex_attr_1.sub(r'<attribute name="\1">True</attribute>', content)
                content = regex_attr_0.sub(r'<attribute name="\1">False</attribute>', content)
                # Replace nolable -> nolabel
                content = regex_nolable.sub('nolabel=', content)
                
                # Replace <field name="view_mode">tree,form</field>
                content = content.replace('>tree,form<', '>list,form<')
                content = content.replace('>tree<', '>list<')
                content = content.replace('>tree,kanban<', '>list,kanban<')
                content = content.replace('>kanban,tree<', '>kanban,list<')
                
                if content != original_content:
                    f.seek(0)
                    f.write(content)
                    f.truncate()
                    print(f"Migrated: {filepath}")

