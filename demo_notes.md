Set this once to reuse the same target account for all tests.

```bash
export COVE_TARGET_ACCOUNT=393170312900
```

```bash
AWS_PROFILE="$BILLING" \
AWS_DEFAULT_REGION=eu-west-1 \
python demo.py use_standard_boto3_credential_chain
```

```python
{'Exceptions': [],
 'FailedAssumeRole': [],
 'Results': [{'Result': {'Caller': '_use_standard_boto3_credential_chain',
                         'Error': None,
                         'Region': 'eu-west-1'}}]}
```

```bash
AWS_PROFILE="$BILLING" \
python demo.py use_standard_boto3_credential_chain
```

```python
{'Exceptions': [],
 'FailedAssumeRole': [],
 'Results': [{'Result': {'Caller': '_use_standard_boto3_credential_chain',
                         'Error': NoRegionError('You must specify a region.'),
                         'Region': None}}]}
```

```bash
COVE_ASSUMING_PROFILE="$BILLING" \
COVE_ASSUMING_REGION=eu-west-1 \
python demo.py use_assuming_session
```

```python
{'Exceptions': [],
 'FailedAssumeRole': [],
 'Results': [{'Result': {'Caller': '_use_assuming_session',
                         'Error': NoRegionError('You must specify a region.'),
                         'Region': None}}]}
```

```bash
COVE_ASSUMING_PROFILE="$BILLING" \
COVE_ASSUMING_REGION=eu-west-1 \
AWS_DEFAULT_REGION=eu-west-1  \
python demo.py use_assuming_session
```

```python
{'Exceptions': [],
 'FailedAssumeRole': [],
 'Results': [{'Result': {'Caller': '_use_assuming_session',
                         'Error': None,
                         'Region': 'eu-west-1'}}]}
```

I think the source of the problem is this. If there is no list of input regions, then cove internally iterates of a list containing `[None]`. This value is eveutally used to instatiate the `CoveSession`'s `region_name`.

https://github.com/connelldave/botocove/blob/af25603060dd3d99f87ac75fe45325fb2cbdbc2d/botocove/cove_host_account.py#L62-L63

```python
        if regions is None:
            self.target_regions = [None]
```

```python
            init_session_args = {
                k: v
                for k, v in [
                    ("aws_access_key_id", creds["AccessKeyId"]),
                    ("aws_secret_access_key", creds["SecretAccessKey"]),
                    ("aws_session_token", creds["SessionToken"]),
                    ("region_name", self.session_information["Region"]),
                ]
                if v is not None
```

I need to rewrite the region tests to cover this.

The wrapped functions don't call any boto3 APIs. In fact they do nothing, just pass.

That's fine for checking input validation and output shapes.

But we need to make real regional API calls to check how botocove is handling the region settings for all the sessions.

Ignoring the `regions` parameter, these are all the ways to set the "default" region.

```text
AWS_DEFAULT_REGION=eu-west-1, assuming_region=None
AWS_DEFAULT_REGION=eu-west-1, assuming_region=Session()
AWS_DEFAULT_REGION=eu-west-1, assuming_region=Session(region_name="eu-west-1")
unset AWS_DEFAULT_REGION, assuming_region=None
unset AWS_DEFAULT_REGION, assuming_region=Session()
unset AWS_DEFAULT_REGION, assuming_region=Session(region_name="eu-west-1")
```

The test cases should cover all these combinations.

See 