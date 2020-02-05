Note: This example is used to create an [issue with pyShacl](https://github.com/RDFLib/pySHACL/issues/37) which
has since been resolved.  But the data graph and shape graph turtle files are kept here as simple examples.

### SHACL example ###

The simple example is lifted from
[SHACL Playground](https://shacl.org/playground/), modified to
demonstrate certain errors that we think should have been reported by ```pyshacl``` but not.
The added "rule" nodes in file ```shape.ttl```  are

```buildoutcfg
schema:hasAddress a owl:AsymmetricProperty,
    owl:IrreflexiveProperty,
    owl:ObjectProperty ;
    rdfs:range schema:PostalAddress ;
    skos:definition "Subject is physically located at the address given by the object" .

schema:AddressShape
    a sh:NodeShape ;
    sh:targetObjectsOf schema:hasAddress ;
    sh:property [
        sh:path schema:hasAddress ;
        sh:class schema:PostalAddress ;
    ] .
```
They define a relationship ```hasAddress``` whose object should be ```PostalAddress```.

In file ```data.ttl```, we think the added triples
```buildoutcfg
ex:Alice a schema:Person .
ex:Bob schema:hasAddress ex:Alice .
```
should cause an error like "Invalid type for object of hasAddress".  But it does not trigger
such error by ```pyshacl```, nor by the SHACL Playground, a JavaScript based validator.

Note if we allow the ```sh:closed true``` constraint in ```shape.ttl```, then the added
triples in ```data.ttl``` do generate an error ```ClosedConstraintComponent``` because ```closed```
constraint says ```Alice``` can't be of any type but ```Person```.

In summary this example either demonstrates our misunderstanding or a flaw in the validating tools with respect to SHACL's ```targetObjectsOf``` target.

Update: The discussion above is reported to ```pyshacl``` as [Issue 37](https://github.com/RDFLib/pySHACL/issues/37)
where a developer suggested two alternatives.  One alternative avoids using ```targetObjectsOf```.  The other one uses ```targetObjectsOf```
but it doesn't appear in the reasoning path of the errors reported by ```pyshacl```.
