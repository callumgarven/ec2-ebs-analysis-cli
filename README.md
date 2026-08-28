# ec2-ebs-analysis-cli

CLI tool to analyse and summarize EBS volume usage per EC2 instance across AWS regions.

# Commands
```
uv run python src/ec2_ebs_analysis_cli/cli.py --help
uv run ruff check --fix . 
uv run ruff format . 
uv run mypy src
```

# Usage

```                                                                                                                                     
 Usage: ec2-ebs-analysis-cli [OPTIONS]                                                                                                             
                                                                                                                                                   
 Inspect EC2 instances and summarise attached EBS volume storage.                                                                                  
                                                                                                                                                   
╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --name        -n      <str>                     Filter instances by Name tag value (uses AWS server-side filter).                               │
│ --region      -r      <str>                     AWS region to query (defaults to AWS_DEFAULT_REGION or eu-west-2).                              │
│                                                 [env var: AWS_DEFAULT_REGION, AWS_REGION]                                                       │
│                                                 [default: eu-west-2]                                                                            │
│ --format      -f      <plaintext|json>          Output serialization format. [default: plaintext]                                               │
│ --sort-by             <ebs_size|name|state|id>  Field used for sorting instances. [default: ebs_size]                                           │
│ --sort-order          <asc|desc>                Sorting direction. [default: asc]                                                               │
│ --help                                          Show this message and exit.                                                                     │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```