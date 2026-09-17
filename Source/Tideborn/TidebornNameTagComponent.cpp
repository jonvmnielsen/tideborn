#include "TidebornNameTagComponent.h"
#include "Components/TextRenderComponent.h"
#include "GameFramework/Actor.h"
#include "Kismet/GameplayStatics.h"
#include "Camera/PlayerCameraManager.h"

UTidebornNameTagComponent::UTidebornNameTagComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
}

void UTidebornNameTagComponent::BeginPlay()
{
	Super::BeginPlay();

	AActor* Owner = GetOwner();
	if (!Owner)
	{
		return;
	}

	TitleText = NewObject<UTextRenderComponent>(Owner, TEXT("TidebornNameTitle"));
	TitleText->SetupAttachment(Owner->GetRootComponent());
	TitleText->RegisterComponent();
	TitleText->SetHorizontalAlignment(EHTA_Center);
	TitleText->SetVerticalAlignment(EVRTA_TextBottom);
	TitleText->SetWorldSize(TitleSize);
	TitleText->SetTextRenderColor(TitleColor);
	TitleText->SetRelativeLocation(FVector(0.f, 0.f, HeightOffset));
	TitleText->SetCollisionEnabled(ECollisionEnabled::NoCollision);

	SubtitleText = NewObject<UTextRenderComponent>(Owner, TEXT("TidebornNameSubtitle"));
	SubtitleText->SetupAttachment(Owner->GetRootComponent());
	SubtitleText->RegisterComponent();
	SubtitleText->SetHorizontalAlignment(EHTA_Center);
	SubtitleText->SetVerticalAlignment(EVRTA_TextTop);
	SubtitleText->SetWorldSize(TitleSize * 0.55f);
	SubtitleText->SetTextRenderColor(FColor(220, 220, 220));
	SubtitleText->SetRelativeLocation(FVector(0.f, 0.f, HeightOffset - 30.f));
	SubtitleText->SetCollisionEnabled(ECollisionEnabled::NoCollision);

	SetLabel(Title, Subtitle);
}

void UTidebornNameTagComponent::SetLabel(const FString& InTitle, const FString& InSubtitle)
{
	Title = InTitle;
	Subtitle = InSubtitle;
	if (TitleText)
	{
		TitleText->SetText(FText::FromString(Title));
	}
	if (SubtitleText)
	{
		SubtitleText->SetText(FText::FromString(Subtitle));
	}
}

void UTidebornNameTagComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	APlayerCameraManager* Cam = UGameplayStatics::GetPlayerCameraManager(GetWorld(), 0);
	if (!Cam)
	{
		return;
	}
	const FVector CamLoc = Cam->GetCameraLocation();
	auto Face = [&](UTextRenderComponent* T)
	{
		if (!T)
		{
			return;
		}
		const FVector ToCam = CamLoc - T->GetComponentLocation();
		T->SetWorldRotation(FRotationMatrix::MakeFromX(ToCam).Rotator());
	};
	Face(TitleText);
	Face(SubtitleText);
}
