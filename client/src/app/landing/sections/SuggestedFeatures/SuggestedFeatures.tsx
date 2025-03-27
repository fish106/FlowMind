import { capitalize } from 'lodash';
import { useEffect, useMemo, useState } from 'react';
import { useParsedSearchParams, useRedirectWithParams } from '@/lib/queryString';
import { useOrFetchFeatureSections } from '@/store/fetchers';
import { TagPreview } from '@/types/workflowAI/models';
import { SuggestedFeaturesList } from './SuggestedFeaturesList';
import { SuggestedFeaturesSearch } from './SuggestedFeaturesSearch';
import { SuggestedFeaturesSections } from './SuggestedFeaturesSections';

export function SuggestedFeatures() {
  const { companyURL } = useParsedSearchParams('companyURL');

  const [selectedTag, setSelectedTag] = useState<TagPreview | undefined>(undefined);

  const { featureSections, isLoading: featureSectionsAreLoading } = useOrFetchFeatureSections();

  const redirectWithParams = useRedirectWithParams();

  useEffect(() => {
    if (!!featureSections && !companyURL) {
      const companySpecificTag: TagPreview | undefined = featureSections
        .find((section) => section.tags.some((tag) => tag.kind === 'company_specific'))
        ?.tags.find((tag) => tag.kind === 'company_specific');

      const lowerCaseURL = companySpecificTag?.name.toLowerCase();

      if (!!lowerCaseURL) {
        redirectWithParams({
          params: {
            companyURL: lowerCaseURL,
          },
        });
      }
    }
  }, [featureSections, companyURL, redirectWithParams]);

  const modifiedFeatureSections = useMemo(() => {
    if (!featureSections) {
      return undefined;
    }

    return featureSections.map((section) => {
      const newTags = [...section.tags];

      if (!!companyURL) {
        // Find and replace company_specific tag
        const companySpecificIndex = newTags.findIndex((tag) => tag.kind === 'company_specific');
        if (companySpecificIndex !== -1) {
          const newTag: TagPreview = {
            name: capitalize(companyURL),
            kind: 'company_specific',
          };
          newTags[companySpecificIndex] = newTag;
          setSelectedTag(newTag);
        }
      } else {
        // Remove company_specific tags with empty name or 'For You'
        const filteredTags = newTags.filter(
          (tag) => !(tag.kind === 'company_specific' && (tag.name === '' || tag.name === 'For You'))
        );
        return { ...section, tags: filteredTags };
      }

      return { ...section, tags: newTags };
    });
  }, [featureSections, companyURL, setSelectedTag]);

  useEffect(() => {
    if (modifiedFeatureSections?.length) {
      setSelectedTag(modifiedFeatureSections[0].tags[0]);
    }
  }, [modifiedFeatureSections, setSelectedTag]);

  return (
    <div className='flex flex-row h-full w-full'>
      <div className='flex w-[212px] h-full border-r border-gray-200 bg-custom-gradient-1 overflow-y-auto overflow-x-hidden'>
        <SuggestedFeaturesSections
          selectedTag={selectedTag}
          setSelectedTag={setSelectedTag}
          featureSections={modifiedFeatureSections}
          isLoading={featureSectionsAreLoading}
        />
      </div>
      <div className='flex flex-col flex-1 h-full'>
        <div className='flex px-16 py-10 border-b border-gray-100'>
          <div className='flex flex-col gap-4 w-full'>
            <div className='text-[18px] text-gray-500 font-normal'>
              What <span className='font-semibold'>AI features</span> can you build for your product?
            </div>
            <SuggestedFeaturesSearch companyURL={companyURL} />
          </div>
        </div>
        <SuggestedFeaturesList tag={selectedTag} companyURL={companyURL} />
      </div>
    </div>
  );
}
