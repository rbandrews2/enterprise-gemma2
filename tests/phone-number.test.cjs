const test=require('node:test'),assert=require('node:assert/strict');
const {normalize}=require('../services/workspace_preview/static/phone-number.js');
test('normalizes US phone formatting and preserves explicit international numbers',()=>{
 for(const value of ['5407970405','(540) 797-0405','1-540-797-0405','+1 540 797 0405'])assert.equal(normalize(value),'+15407970405');
 assert.equal(normalize('+44 20 7946 0958'),'+442079460958');
});
test('rejects malformed values rather than inventing country codes',()=>{
 for(const value of ['', '555', 'number@example.org','++15407970405','00442079460958','+0123456789','+15407970405 ext 2'])assert.equal(normalize(value),null,value);
});
