/*=========================================================================

  Program:   BioImageXD
  Module:    $RCSfile: vtkImageColorMerge.cxx,v $

 Copyright (C) 2005  BioImageXD Project
 See CREDITS.txt for details
 
 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


=========================================================================*/
#include "vtkImageColorMerge.h"

#include "vtkImageData.h"
#include "vtkObjectFactory.h"
#include "vtkInformation.h"
#include "vtkInformationVector.h"
#include "vtkStreamingDemandDrivenPipeline.h"


vtkCxxRevisionMacro(vtkImageColorMerge, "$Revision: 1.25 $");
vtkStandardNewMacro(vtkImageColorMerge);

//----------------------------------------------------------------------------
vtkImageColorMerge::vtkImageColorMerge()
{
    this->ITFCount = this->CTFCount = 0;
    this->AverageMode = 0;
    this->MaximumMode = 0;
    this->LuminanceMode = 0;
    this->AverageThreshold = 10;
	this->SetNumberOfThreads(1);
}

//----------------------------------------------------------------------------
vtkImageColorMerge::~vtkImageColorMerge()
{
}

void vtkImageColorMerge::ClearItfs() {
    while(this->ITFCount) {
        this->IntensityTransferFunctions[--this->ITFCount] = NULL;
    }
}

void vtkImageColorMerge::ClearCtfs()
{
  while (this->CTFCount)
	this->ColorTransferFunctions[--this->CTFCount] = NULL;
}

//----------------------------------------------------------------------------
// This templated function executes the filter for any type of data.
template <class T>
void vtkImageColorMergeExecute(vtkImageColorMerge *self, int id,int NumberOfInputs,
                           vtkImageData **inData,vtkImageData*outData,int outExt[6],
                            T*)
{
    int i;
    vtkIdType inIncX,inIncY,inIncZ;
    vtkIdType outIncX,outIncY,outIncZ;
    int maxX,maxY,maxZ;
    int idxX = 0,idxY = 0,idxZ = 0;
    unsigned long count = 0;
    unsigned long target;    

    unsigned char **ctfs;        
    int **itfs;
    int itfCount = self->GetITFCount();
    
    int BuildAlpha = self->GetBuildAlpha();
    int AvgThreshold = self->GetAverageThreshold();
    int MaxMode = self->GetMaximumMode();                   
    int AvgMode = self->GetAverageMode();
    int LuminanceMode = self->GetLuminanceMode();
    if (!MaxMode && !AvgMode) AvgMode = 1;    
    
    if (self->GetCTFCount() != NumberOfInputs) {
        vtkErrorWithObjectMacro(self,<< "Number of lookup tables ("<< self->GetCTFCount() <<") != number of inputs"<<NumberOfInputs);
    }
    if (itfCount && itfCount != NumberOfInputs) {
        vtkErrorWithObjectMacro(self, "Number of ITFs ("<<itfCount<<") != number of inputs"<<NumberOfInputs);
    }
    
    T** inPtrs;
    unsigned char* outPtr;
    itfs = new int*[NumberOfInputs];
    ctfs = new unsigned char*[NumberOfInputs];
    
    inPtrs = new T*[NumberOfInputs];
    int moreThanOne = 0;
    int *scalarComponents = new int[NumberOfInputs];
    int allIdentical = 1;
    
    vtkIntensityTransferFunction* itf;
    vtkColorTransferFunction* ctf;
    int isIdentical = 0;

    const unsigned char* map;
    
    for (i = 0; i < NumberOfInputs; i++) {
        ctfs[i] = 0;
        itfs[i] = 0;
        scalarComponents[i] = inData[i]->GetNumberOfScalarComponents();        
        inPtrs[i] = (T*)inData[i]->GetScalarPointerForExtent(outExt);
        if (scalarComponents[i] > 1) {
            moreThanOne=1;
            continue;
        }

        isIdentical = 1;
        ctf = self->GetColorTransferFunction(i);
        double range[2];
        ctf->GetRange(range);
        int n = int(range[1]-range[0])+1;
//  n++;
        map = ctf->GetTable(range[0],range[1],n);
        //ctfs[i] = self->GetColorTransferFunction(i)->GetTable(0,255,256);
        ctfs[i] = new unsigned char[n*3];

        if (itfCount) {
            itf = self->GetIntensityTransferFunction(i);
            itfs[i] = itf->GetDataPointer();
            
            if (!itf->IsIdentical()) {
                isIdentical = 0;
                allIdentical = 0;                
            }
        }

        for (int x = 0,xx = 0; xx < n; xx++) {
		  if (!isIdentical) {
			x = itfs[i][xx];
		  }
		  else x = xx;

		  ctfs[i][3*xx] = map[3*x];
		  ctfs[i][3*xx+1] = map[3*x+1];
		  ctfs[i][3*xx+2] = map[3*x+2];
        } 
    }

    outPtr=(unsigned char*)outData->GetScalarPointerForExtent(outExt);
    
    inData[0]->GetContinuousIncrements(outExt,inIncX, inIncY, inIncZ);
    outData->GetContinuousIncrements(outExt,outIncX, outIncY, outIncZ);
    maxX = outExt[1] - outExt[0];
    maxY = outExt[3] - outExt[2];
    maxZ = outExt[5] - outExt[4];

    int currScalar = 0;
    int alphaScalar; 
    int n = 0;
    //maxval=int(pow(2.0f,8.0f*sizeof(unsigned char)))-1;
    unsigned char maxval=255;
    
    //maxX *= (inData[0]->GetNumberOfScalarComponents());
    char progressText[200];
    
    int r = 0,g = 0,b = 0;
    
    target = (unsigned long)((maxZ+1)*(maxY+1)/50.0);
    target++;
    
    for (idxZ = 0; idxZ <= maxZ; idxZ++ ) {        
//        printf("id=%d Set progress text to %s\n",id, progressText);
//        printf("id=%d, Setting progress to %d / %d = %f\n",id,idxZ+1,maxZ+1,(idxZ+1)/float(maxZ+1));
         sprintf(progressText,"Merging channels (slice %d / %d)",idxZ+1,maxZ+1);
         self->SetProgressText(progressText);

        for (idxY = 0; !self->AbortExecute &&  idxY <= maxY; idxY++ ) {
            if (!id)
            {
                if (!(count%target))
                {
                    self->UpdateProgress(count/(50.0*target));
                }
                count++;
           }  
          for (idxX = 0; idxX <= maxX; idxX++ ) {
            alphaScalar =  currScalar = n = 0;
//            if(id==1)printf("idxX = %d, idxY = %d, idxZ = %d\n",idxX, idxY, idxZ);
            for (i = 0; i < NumberOfInputs; i++ ) {
                currScalar = (int)*inPtrs[i];
//                if(id==1)printf("thread 1 got as input %d\n",currScalar);
                
                if (BuildAlpha) {
                  if (MaxMode) {
                        if (alphaScalar < currScalar) {
                            alphaScalar = currScalar;
                        }
                    // If the alpha channel should be in "average mode"
                    // then we take an average of all the scalars in the
                    // current voxel that are above the AverageThreshold
                  }
				  else if (AvgMode && currScalar > AvgThreshold) {
                        n++;
                        alphaScalar += currScalar;
                  }
                }
                if (!(moreThanOne && scalarComponents[i] > 1)) {
                    r += ctfs[i][3*currScalar];
                    g += ctfs[i][3*currScalar+1];
                    b += ctfs[i][3*currScalar+2];

                }
				else {
                    r += currScalar;
                    inPtrs[i]++;
                    g += (int)*inPtrs[i];
                    inPtrs[i]++;
                    b += (int)*inPtrs[i];
                }

                inPtrs[i]++;
            }

            *outPtr++ = (r > maxval ? maxval : (unsigned char)r);
            *outPtr++ = (g > maxval ? maxval : (unsigned char)g);
            *outPtr++ = (b > maxval ? maxval : (unsigned char)b);
            
            if (BuildAlpha) {
                if (AvgMode && n > 0) alphaScalar /= n;
                else if(LuminanceMode) {
                    alphaScalar = int(0.30*r + 0.59*g + 0.11*b);
                }   
                    
                if (alphaScalar > maxval) alphaScalar=maxval;
                *outPtr++ = (unsigned char)alphaScalar;
            }
            r=g=b=0;
          }
          
          for (i = 0; i < NumberOfInputs; i++ ) {
              inPtrs[i] += inIncY;
          }
          outPtr += outIncY;
        }  
        for(i = 0; i < NumberOfInputs; i++ ) {
          inPtrs[i] += inIncZ;
        }
        outPtr += outIncZ;      
    }

    for (int i = 0; i < NumberOfInputs; i++) {        
        if (ctfs[i])
            delete[] ctfs[i];
    }

    delete[] scalarComponents;
    delete[] inPtrs;
    delete[] ctfs;
    delete[] itfs;
}


//----------------------------------------------------------------------------
// This method is passed a input and output regions, and executes the filter
// algorithm to fill the output from the inputs.
// It just executes a switch statement to call the correct function for
// the regions data types.
void vtkImageColorMerge::ThreadedRequestData (
  vtkInformation * vtkNotUsed( request ),
  vtkInformationVector** vtkNotUsed( inputVector ),
  vtkInformationVector * vtkNotUsed( outputVector ),
  vtkImageData ***inData,
  vtkImageData **outData,
  int outExt[6], int id)
{
//    printf("vtkImageColorMerge ThreadedRequestData outExt=%d,%d,%d,%d,%d,%d\n",outExt[0],outExt[1],outExt[2],outExt[3],outExt[4],outExt[5]);
  if (inData[0][0] == NULL)
    {
    vtkErrorMacro(<< "Input " << 0 << " must be specified.");
    return;
    }
/*
  // this filter expects that input is the same type as output.
  if (inData[0][0]->GetScalarType() != outData[0]->GetScalarType())
    {
    vtkErrorMacro(<< "Execute: input ScalarType, "
                  << inData[0][0]->GetScalarType()
                  << ", must match out ScalarType "
                  << outData[0]->GetScalarType());
    return;
    }
*/
//  printf("Number of connections=%d, outExt=%d,%d,%d,%d,%d,%d\n",this->GetNumberOfInputConnections(0),
//                 outExt[0],outExt[1],outExt[2],outExt[3],outExt[4],outExt[5]);

    switch (inData[0][0]->GetScalarType())
  {
    vtkTemplateMacro(vtkImageColorMergeExecute(this, id,
                    this->GetNumberOfInputConnections(0),inData[0],
                    outData[0], outExt,static_cast<VTK_TT *>(0)));
  default:
    vtkErrorMacro(<< "Execute: Unknown ScalarType");
  return;
  }
  //printf("ThreadedRequestData done merging\n");

}

int vtkImageColorMerge::FillInputPortInformation(
  int port, vtkInformation* info)
{
  info->Set(vtkAlgorithm::INPUT_IS_REPEATABLE(), 1);

  info->Set(vtkAlgorithm::INPUT_REQUIRED_DATA_TYPE(), "vtkImageData");

  return 1;
}

// The output extent is the same as the input extent.
int vtkImageColorMerge::RequestInformation (
  vtkInformation * vtkNotUsed(request),
  vtkInformationVector **inputVector,
  vtkInformationVector *outputVector)
{
  // get the info objects
  vtkInformation* outInfo = outputVector->GetInformationObject(0);
  vtkInformation *inInfo = inputVector[0]->GetInformationObject(0);

  int ext[6], ext2[6], idx;

  inInfo->Get(vtkStreamingDemandDrivenPipeline::WHOLE_EXTENT(),ext);
  outInfo->Set(vtkStreamingDemandDrivenPipeline::WHOLE_EXTENT(),ext,6);
    
  int n = 4;
  if (!this->BuildAlpha) n = 3;

  vtkDataObject::SetPointDataActiveScalarInfo(outInfo, VTK_UNSIGNED_CHAR,n);
  return 1;
}


//----------------------------------------------------------------------------
void vtkImageColorMerge::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os, indent);
}
