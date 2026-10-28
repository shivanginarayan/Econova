// Workspace-local ES256 keys for the portable standalone server. No key output.
import {generateKeyPairSync} from 'node:crypto';
import {existsSync,mkdirSync,writeFileSync} from 'node:fs';
mkdirSync('data/spacetime-keys',{recursive:true});
if(!existsSync('data/spacetime-keys/private.pem')){
 const {publicKey,privateKey}=generateKeyPairSync('ec',{namedCurve:'prime256v1',publicKeyEncoding:{type:'spki',format:'pem'},privateKeyEncoding:{type:'pkcs8',format:'pem'}});
 writeFileSync('data/spacetime-keys/private.pem',privateKey);writeFileSync('data/spacetime-keys/public.pem',publicKey);
}
console.log('Local database signing keys ready.');
